-- Phase 5 follow-up: order claim_and_publish_digest issue items from p_material_ids (CR-01).
-- Idempotent: DROP + CREATE OR REPLACE; no table wipes.
-- Assigns digest_issue_items.position inside the same PL/pgSQL transaction as the claim,
-- so a failed RPC cannot leave mutated shortlist ranks from a separate Python UPDATE.

-- Drop the migration-005 signature (no p_material_ids) before recreating with the new arg.
drop function if exists public.claim_and_publish_digest(
  bigint, timestamptz, text, text, text, int
);

create or replace function public.claim_and_publish_digest(
  p_batch_id bigint,
  p_sent_at timestamptz,
  p_period_label text,
  p_title text,
  p_delivery_status text default 'stubbed',
  p_recipient_count int default 0,
  p_material_ids bigint[] default null
)
returns jsonb
language plpgsql
security invoker
set search_path = public
as $$
declare
  v_batch public.digest_shortlist_batches%rowtype;
  v_issue_id bigint;
  v_issue_number int;
  v_issue_url text;
  v_item_count int := 0;
begin
  update public.digest_shortlist_batches b
  set sent_at = p_sent_at
  where b.id = p_batch_id
    and b.sent_at is null
  returning b.* into v_batch;

  if not found then
    raise exception 'claim_and_publish_digest: batch % already sent or missing', p_batch_id
      using errcode = 'P0001';
  end if;

  select coalesce(max(i.number), 0) + 1 into v_issue_number
  from public.digest_issues i;

  insert into public.digest_issues (number, period_label, title, published_at)
  values (v_issue_number, p_period_label, p_title, p_sent_at)
  returning id into v_issue_id;

  if p_material_ids is not null and cardinality(p_material_ids) > 0 then
    -- Admin-provided order (G-05-1): position from array ordinality inside this transaction.
    insert into public.digest_issue_items (issue_id, material_id, position)
    select v_issue_id, mid, ord::int
    from unnest(p_material_ids) with ordinality as t(mid, ord)
    join public.digest_shortlist_items si
      on si.batch_id = p_batch_id and si.material_id = mid
    join public.materials m on m.id = mid
    where si.decision = 'approved'
      and m.status = 'ready';
  else
    -- Default: shortlist rank order for approved∩ready.
    insert into public.digest_issue_items (issue_id, material_id, position)
    select v_issue_id, si.material_id, si.rank
    from public.digest_shortlist_items si
    join public.materials m on m.id = si.material_id
    where si.batch_id = p_batch_id
      and si.decision = 'approved'
      and m.status = 'ready'
    order by si.rank;
  end if;

  get diagnostics v_item_count = row_count;
  if v_item_count = 0 then
    raise exception 'claim_and_publish_digest: empty approved∩ready pool for batch %', p_batch_id
      using errcode = 'check_violation';
  end if;

  v_issue_url := '/issues/' || v_issue_number::text;

  update public.digest_shortlist_batches
  set
    delivery_status = p_delivery_status,
    recipient_count = coalesce(p_recipient_count, 0),
    published_issue_id = v_issue_id,
    issue_url = v_issue_url
  where id = p_batch_id;

  return jsonb_build_object(
    'batch_id', p_batch_id,
    'issue_id', v_issue_id,
    'issue_number', v_issue_number,
    'issue_url', v_issue_url,
    'delivery_status', p_delivery_status,
    'recipient_count', coalesce(p_recipient_count, 0),
    'item_count', v_item_count
  );
end;
$$;

revoke all on function public.claim_and_publish_digest(
  bigint, timestamptz, text, text, text, int, bigint[]
) from public;
revoke all on function public.claim_and_publish_digest(
  bigint, timestamptz, text, text, text, int, bigint[]
) from anon, authenticated;
grant execute on function public.claim_and_publish_digest(
  bigint, timestamptz, text, text, text, int, bigint[]
) to service_role;
