"""send_digest — validate, atomic claim+publish, stub mail (ADMIN-03/07/08, D-85…D-90)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Sequence

from backend.application.ports.digest_publisher import DigestPublisher
from backend.application.ports.mailer import Mailer
from backend.application.ports.ping_recorder import PingRecorder
from backend.application.ports.profile_repository import ProfileRepository
from backend.application.ports.shortlist_repository import ShortlistRepository
from backend.application.use_cases.email_render import DEFAULT_SITE_URL, render_email_html
from backend.application.use_cases.preview_digest_email import (
    PreviewBlock,
    PreviewMaterialBlock,
    _html_content_blocks,
    compose_digest_body,
    compose_digest_segments,
)
from backend.domain.errors import (
    AlreadySentError,
    DraftInSendPoolError,
    EmptySendPoolError,
    InvalidPreviewCompositionError,
    InvalidSendOrderError,
    MailDeliveryError,
    PersistenceError,
)
from backend.domain.shortlist import ShortlistItem, visible_shortlist_items

logger = logging.getLogger(__name__)

_ALLOWED_DELIVERY_STATUSES = frozenset({"stubbed", "sent", "partial", "failed"})
"""D-07: the only mailer statuses `_compose_delivery_message` may render; anything else is
treated as `failed` so an unknown token can never be promoted to a delivery claim (IN-01/D-09)."""


@dataclass(frozen=True)
class SendDigestResult:
    batch_id: int
    issue_number: int
    issue_url: str
    delivery_status: str
    recipient_count: int
    delivered_count: int
    message: str


def _compose_delivery_message(
    *,
    delivery_status: str,
    recipient_count: int,
    delivered_count: int,
) -> str:
    """Two honest sentences: publish confirmation + delivery line (D-09/D-12 / MAIL-03)."""
    if delivery_status == "stubbed":
        return (
            "Выпуск опубликован. "
            f"Доставка писем: stub ({delivered_count} из {recipient_count})"
        )
    if delivery_status == "partial":
        return (
            "Выпуск опубликован. "
            f"Доставлено {delivered_count} из {recipient_count} (частично)"
        )
    if delivery_status == "failed":
        return (
            "Выпуск опубликован. "
            f"Письма не доставлены ({delivered_count} из {recipient_count})"
        )
    # sent (D-07): an empty live audience is honestly `sent` with N=0 (RESEARCH Q3).
    if recipient_count == 0:
        return "Выпуск опубликован. Получателей нет (0 из 0)"
    return f"Выпуск опубликован. Доставлено {delivered_count} из {recipient_count}"


def _approved_drafts(items: tuple[ShortlistItem, ...]) -> list[int]:
    return [
        item.material_id
        for item in items
        if item.decision == "approved" and item.material_status == "draft"
    ]


def _approved_ready(items: tuple[ShortlistItem, ...]) -> list[ShortlistItem]:
    return sorted(
        [
            item
            for item in items
            if item.decision == "approved" and item.material_status == "ready"
        ],
        key=lambda item: item.rank,
    )


def _ordered_pool(
    pool: list[ShortlistItem],
    material_ids: list[int] | None,
    *,
    batch_id: int,
) -> list[ShortlistItem]:
    """Validate optional material_ids as exact permutation; return publication order."""
    if material_ids is None:
        return pool
    pool_ids = {item.material_id for item in pool}
    if len(material_ids) != len(pool_ids) or set(material_ids) != pool_ids:
        raise InvalidSendOrderError(batch_id=batch_id)
    by_id = {item.material_id: item for item in pool}
    return [by_id[mid] for mid in material_ids]


def _material_ids_from_blocks(blocks: Sequence[PreviewBlock] | None) -> list[int] | None:
    if blocks is None:
        return None
    ids = [
        block.material_id
        for block in blocks
        if isinstance(block, PreviewMaterialBlock)
    ]
    return ids if ids else None


def send_digest(
    shortlist: ShortlistRepository,
    publisher: DigestPublisher,
    mailer: Mailer,
    pings: PingRecorder,
    profiles: ProfileRepository,
    *,
    actor_user_id: str,
    now: datetime | None = None,
    material_ids: list[int] | None = None,
    intro: str = "",
    blocks: Sequence[PreviewBlock] | None = None,
    site_url: str = DEFAULT_SITE_URL,
) -> SendDigestResult:
    """Validate pool → atomic claim+publish → mail → audit (D-88 mandatory publish-on-send).

    CR-01/WR-01: the claim, digest_issues publish, and delivery-column stamp are a single
    transaction inside ``DigestPublisher.claim_and_publish`` (migration 005/006 RPC on live),
    so a publish failure can never leave a batch stamped ``sent_at`` with no issue.

    When ``material_ids`` is provided it must be an exact permutation of the approved∩ready
    pool; that order becomes publication and mail order (G-05-1).

    WR-02: optional ``intro`` + ``blocks`` compose the mail body with the same rules as
    preview (plus an issue URL header). HTML uses shared ``render_email_html`` (D-07);
    issue URL stays in the plain wrapper only (D-11).

    CR-02: after a successful claim+publish, mail and audit are best-effort — failures are
    logged and must not convert an already-published digest into a failed send response.
    """
    clock = now or datetime.now(timezone.utc)
    batch = shortlist.get_current_batch()
    if batch is None:
        # No unsent batch. Distinguish "already sent this week" (D-89 → AlreadySentError/409,
        # «Уже отправлено») from a genuinely empty pool (→ EmptySendPoolError/400). WR-03: both
        # live and in-memory hide sent batches from get_current_batch, so consult the latest.
        latest = shortlist.get_latest_batch()
        if latest is not None and latest.sent_at is not None:
            raise AlreadySentError(latest.id)
        raise EmptySendPoolError()

    drafts = _approved_drafts(visible_shortlist_items(batch.items))
    if drafts:
        raise DraftInSendPoolError(drafts, batch_id=batch.id)

    pool = _approved_ready(visible_shortlist_items(batch.items))
    if not pool:
        raise EmptySendPoolError(batch_id=batch.id)

    # Prefer explicit material_ids; otherwise derive order from composition blocks.
    effective_ids = material_ids if material_ids is not None else _material_ids_from_blocks(blocks)
    ordered = _ordered_pool(pool, effective_ids, batch_id=batch.id)
    ordered_ids = [item.material_id for item in ordered]

    try:
        materials, body_segments = compose_digest_segments(
            pool=ordered,
            blocks=blocks,
            site_url=site_url,
        )
    except InvalidPreviewCompositionError as exc:
        raise InvalidSendOrderError(batch_id=batch.id) from exc
    except EmptySendPoolError as exc:
        raise EmptySendPoolError(batch_id=batch.id) from exc

    # MAIL-01/D-01/D-02: resolve the audience from profiles BEFORE the claim so the planned
    # count M can be stamped on the batch (D-06 option i) and echoed to the mailer.
    recipients = list(profiles.list_digest_recipients())
    recipient_count = len(recipients)

    publication = publisher.claim_and_publish(
        batch_id=batch.id,
        sent_at=clock,
        period_label=batch.week_start.isoformat(),
        title=f"Digest CDS — {batch.week_start.isoformat()}",
        material_ids=ordered_ids,
        recipient_count=recipient_count,
    )

    issue_url = publication.issue_url
    composed = compose_digest_body(intro=intro, segments=body_segments)
    subject = f"Digest CDS — выпуск {publication.issue_number}"
    body_text = (
        f"Новый выпуск Digest CDS №{publication.issue_number}.\n"
        f"Читать: {issue_url}\n\n"
        f"{composed}"
    )
    body_html = render_email_html(
        intro=intro,
        blocks=_html_content_blocks(ordered_materials=materials, blocks=blocks),
        site_url=site_url,
    )
    mail_result: dict[str, object] | None = None
    try:
        mail_result = mailer.send_digest(
            batch_id=publication.batch_id,
            issue_url=issue_url,
            subject=subject,
            body_text=body_text,
            recipient_count=recipient_count,
            recipients=recipients,
            body_html=body_html,
        )
    except (MailDeliveryError, PersistenceError):
        logger.exception(
            "digest_send mail failed after publish batch_id=%s",
            publication.batch_id,
        )

    if mail_result is not None:
        raw_status = str(mail_result.get("delivery_status") or "")
        # IN-01/D-09: validate the mailer token; an unknown/absent status is reported
        # conservatively as `failed` instead of being rendered as a successful delivery.
        delivery_status = (
            raw_status if raw_status in _ALLOWED_DELIVERY_STATUSES else "failed"
        )
        raw_delivered = mail_result.get("delivered_count")
        delivered_count = raw_delivered if isinstance(raw_delivered, int) else 0
        stop_reason = mail_result.get("stop_reason")
    else:
        # MAIL-04 / D-88: a mail failure after publish is contained — the digest stays
        # published and the response honestly reports a failed delivery (never 500).
        delivery_status = "failed"
        delivered_count = 0
        stop_reason = None

    message = _compose_delivery_message(
        delivery_status=delivery_status,
        recipient_count=recipient_count,
        delivered_count=delivered_count,
    )

    ping_payload: dict[str, object] = {
        "action": "send",
        "batch_id": publication.batch_id,
        "issue_number": publication.issue_number,
        "issue_url": issue_url,
        "delivery_status": delivery_status,
        "recipient_count": recipient_count,
        "delivered_count": delivered_count,
    }
    if stop_reason:
        ping_payload["stop_reason"] = stop_reason

    try:
        pings.record(
            user_id=actor_user_id,
            kind="digest_send",
            payload=ping_payload,
        )
    except PersistenceError:
        logger.exception(
            "digest_send audit failed after publish batch_id=%s",
            publication.batch_id,
        )

    return SendDigestResult(
        batch_id=publication.batch_id,
        issue_number=publication.issue_number,
        issue_url=issue_url,
        delivery_status=delivery_status,
        recipient_count=recipient_count,
        delivered_count=delivered_count,
        message=message,
    )
