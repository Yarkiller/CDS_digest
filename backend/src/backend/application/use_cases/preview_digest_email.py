"""Build digest email preview for approved∩ready materials (ADMIN-04, D-86, G-05-1)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from backend.application.ports.shortlist_repository import ShortlistRepository
from backend.application.use_cases.email_render import DEFAULT_SITE_URL, render_email_html
from backend.domain.errors import EmptySendPoolError, InvalidPreviewCompositionError
from backend.domain.shortlist import ShortlistItem, visible_shortlist_items


@dataclass(frozen=True)
class PreviewMaterialBlock:
    material_id: int


@dataclass(frozen=True)
class PreviewTextBlock:
    text: str


PreviewBlock = PreviewMaterialBlock | PreviewTextBlock


@dataclass(frozen=True)
class DigestPreviewItem:
    material_id: int
    rank: int
    title: str


@dataclass(frozen=True)
class DigestEmailPreview:
    batch_id: int
    subject: str
    body: str
    items: tuple[DigestPreviewItem, ...]
    html: str


def _approved_ready(items: tuple[ShortlistItem, ...]) -> list[ShortlistItem]:
    return sorted(
        [
            item
            for item in items
            if item.decision == "approved" and item.material_status == "ready"
        ],
        key=lambda item: item.rank,
    )


def compose_digest_body(*, intro: str, segments: list[str]) -> str:
    parts: list[str] = []
    trimmed = intro.strip()
    if trimmed:
        parts.append(trimmed)
    parts.extend(segments)
    return "\n".join(parts) + ("\n" if parts else "")


# Back-compat alias used by older call sites / tests.
_compose_body = compose_digest_body


def _plain_material_segment(item: ShortlistItem, *, site_url: str) -> str:
    """Title + optional dek + absolute reader URL for StubMailer log honesty (Q3).

    W-2: a blank/whitespace slug emits no reader URL — never a dead `/materials/` link.
    """
    parts = [item.title]
    if item.dek and item.dek.strip():
        parts.append(item.dek.strip())
    base = site_url.rstrip("/")
    slug = (item.slug or "").strip()
    if slug:
        parts.append(f"{base}/materials/{slug}")
    return "\n".join(parts)


def compose_digest_segments(
    *,
    pool: list[ShortlistItem],
    blocks: Sequence[PreviewBlock] | None,
    site_url: str = DEFAULT_SITE_URL,
) -> tuple[list[ShortlistItem], list[str]]:
    """Build ordered materials + body segments from optional composition blocks.

    Shared by preview and send so StubMailer/SMTP bodies match «Превью письма».
    Plain interstitial segments preserve internal ``\\n\\n`` after outer strip (D-14).
    """
    by_id = {item.material_id: item for item in pool}

    if blocks is None or len(blocks) == 0:
        return pool, [_plain_material_segment(item, site_url=site_url) for item in pool]

    ordered_materials: list[ShortlistItem] = []
    body_segments: list[str] = []
    for block in blocks:
        if isinstance(block, PreviewTextBlock):
            # Outer strip only — keep internal blank lines (D-14).
            text = block.text.strip()
            if text:
                body_segments.append(text)
            continue
        if not isinstance(block, PreviewMaterialBlock):
            raise InvalidPreviewCompositionError()
        item = by_id.get(block.material_id)
        if item is None:
            raise InvalidPreviewCompositionError(material_id=block.material_id)
        ordered_materials.append(item)
        body_segments.append(_plain_material_segment(item, site_url=site_url))
    if not ordered_materials:
        raise EmptySendPoolError()
    return ordered_materials, body_segments


def _html_content_blocks(
    *,
    ordered_materials: list[ShortlistItem],
    blocks: Sequence[PreviewBlock] | None,
) -> list[dict[str, object]]:
    if blocks is None or len(blocks) == 0:
        return [
            {
                "kind": "material",
                "title": item.title,
                "dek": item.dek,
                "slug": item.slug or "",
            }
            for item in ordered_materials
        ]
    by_id = {item.material_id: item for item in ordered_materials}
    # Material blocks may appear in composition before we finish collecting —
    # rebuild lookup from full ordered list after compose; also allow by_id from pool.
    content: list[dict[str, object]] = []
    for block in blocks:
        if isinstance(block, PreviewTextBlock):
            content.append({"kind": "text", "text": block.text})
            continue
        item = by_id.get(block.material_id)
        if item is None:
            continue
        content.append(
            {
                "kind": "material",
                "title": item.title,
                "dek": item.dek,
                "slug": item.slug or "",
            }
        )
    return content


def preview_digest_email(
    shortlist: ShortlistRepository,
    *,
    intro: str = "",
    blocks: Sequence[PreviewBlock] | None = None,
    site_url: str = DEFAULT_SITE_URL,
) -> DigestEmailPreview:
    """Return subject/body/html/items for approved∩ready; never marks sent_at.

    When ``blocks`` is None or empty, materials default to approved∩ready by rank.
    Explicit material blocks must all be in that pool; text blocks are interstitial copy.
    """
    batch = shortlist.get_current_batch()
    if batch is None:
        raise EmptySendPoolError()

    pool = _approved_ready(visible_shortlist_items(batch.items))
    if not pool:
        raise EmptySendPoolError(batch_id=batch.id)

    try:
        ordered_materials, body_segments = compose_digest_segments(
            pool=pool,
            blocks=blocks,
            site_url=site_url,
        )
    except EmptySendPoolError:
        raise EmptySendPoolError(batch_id=batch.id) from None

    preview_items = tuple(
        DigestPreviewItem(
            material_id=item.material_id,
            rank=position,
            title=item.title,
        )
        for position, item in enumerate(ordered_materials, start=1)
    )
    subject = f"Digest CDS — превью ({batch.week_start.isoformat()})"
    body = _compose_body(intro=intro, segments=body_segments)
    html = render_email_html(
        intro=intro,
        blocks=_html_content_blocks(ordered_materials=ordered_materials, blocks=blocks),
        site_url=site_url,
    )
    return DigestEmailPreview(
        batch_id=batch.id,
        subject=subject,
        body=body,
        items=preview_items,
        html=html,
    )
