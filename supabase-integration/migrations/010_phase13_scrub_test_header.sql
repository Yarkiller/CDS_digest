-- Phase 13: defensive scrub of closed ban tokens from materials text (ADUX-04, D-20).
-- Closed list (D-18): test-header, test_header, testheader (case-insensitive via lower()).
-- Idempotent UPDATE — 0-row apply is OK when live rows are already clean.
-- Shared VM: apply once via Studio SQL / psql / supabase db push — never reset.
-- Assert-only helpers remain in Python/JS; do not filter at render time (D-17).

-- Scrub title / dek / body_markdown / provenance_label when any closed token matches.
update public.materials
set
  title = regexp_replace(title, '(?i)test[-_]?header', '', 'g'),
  dek = case
    when dek is null then null
    else regexp_replace(dek, '(?i)test[-_]?header', '', 'g')
  end,
  body_markdown = case
    when body_markdown is null then null
    else regexp_replace(body_markdown, '(?i)test[-_]?header', '', 'g')
  end,
  provenance_label = case
    when provenance_label is null then null
    else regexp_replace(provenance_label, '(?i)test[-_]?header', '', 'g')
  end
where
  lower(coalesce(title, '')) like '%test-header%'
  or lower(coalesce(title, '')) like '%test_header%'
  or lower(coalesce(title, '')) like '%testheader%'
  or lower(coalesce(dek, '')) like '%test-header%'
  or lower(coalesce(dek, '')) like '%test_header%'
  or lower(coalesce(dek, '')) like '%testheader%'
  or lower(coalesce(body_markdown, '')) like '%test-header%'
  or lower(coalesce(body_markdown, '')) like '%test_header%'
  or lower(coalesce(body_markdown, '')) like '%testheader%'
  or lower(coalesce(provenance_label, '')) like '%test-header%'
  or lower(coalesce(provenance_label, '')) like '%test_header%'
  or lower(coalesce(provenance_label, '')) like '%testheader%';

-- Verify after apply (expect 0):
-- select count(*) as remaining_ban_hits
-- from public.materials
-- where lower(coalesce(title, '')) like '%test-header%'
--    or lower(coalesce(title, '')) like '%test_header%'
--    or lower(coalesce(title, '')) like '%testheader%'
--    or lower(coalesce(dek, '')) like '%test-header%'
--    or lower(coalesce(dek, '')) like '%test_header%'
--    or lower(coalesce(dek, '')) like '%testheader%'
--    or lower(coalesce(body_markdown, '')) like '%test-header%'
--    or lower(coalesce(body_markdown, '')) like '%test_header%'
--    or lower(coalesce(body_markdown, '')) like '%testheader%'
--    or lower(coalesce(provenance_label, '')) like '%test-header%'
--    or lower(coalesce(provenance_label, '')) like '%test_header%'
--    or lower(coalesce(provenance_label, '')) like '%testheader%';
