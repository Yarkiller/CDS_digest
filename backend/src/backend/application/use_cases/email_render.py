"""Shared digest email HTML renderers (ADUX-02/03, D-07/D-11/D-13).

Pure helpers — no FastAPI/Supabase. Stdlib html.escape only.
Ban helper must not be imported here for filtering (D-17).
"""

from __future__ import annotations

import html
from typing import Any, Mapping, Sequence

DEFAULT_SITE_URL = "http://127.0.0.1:5173"


def render_interstitial_html(text: str) -> str:
    """Escape + split interstitial/intro text into HTML paragraphs (D-13)."""
    trimmed = text.strip()
    if not trimmed:
        return ""
    safe = html.escape(trimmed, quote=True)
    paragraphs = safe.split("\n\n")
    parts: list[str] = []
    for para in paragraphs:
        if not para:
            continue
        parts.append("<p>" + para.replace("\n", "<br>") + "</p>")
    return "".join(parts)


def render_material_email_block(
    *,
    title: str,
    dek: str | None,
    slug: str,
    site_url: str = DEFAULT_SITE_URL,
) -> str:
    """Title + optional dek + Читать → absolute material link (D-11).

    W-2: a blank/whitespace slug emits no reader link — never a dead `/materials/` href.
    """
    base = site_url.rstrip("/")
    parts = [f"<h2>{html.escape(title, quote=True)}</h2>"]
    if dek and dek.strip():
        parts.append(f"<p>{html.escape(dek.strip(), quote=True)}</p>")
    clean_slug = slug.strip()
    if clean_slug:
        # This builder is shared by preview_digest_email and send_digest, so the href
        # stays reader-facing (`{base}/materials/{slug}`) for the preview and the real
        # send alike — D-11 satisfies the preview-CTA requirement behaviourally, through
        # `target`/`rel` plus the widened iframe sandbox, never by leaking an admin URL
        # into the mail ordinary readers receive (T-18-06).
        href = html.escape(f"{base}/materials/{clean_slug}", quote=True)
        parts.append(
            f'<p><a href="{href}" target="_blank" rel="noopener noreferrer">Читать →</a></p>'
        )
    return "".join(parts)


def render_email_html(
    *,
    intro: str = "",
    blocks: Sequence[Mapping[str, Any]] | None = None,
    site_url: str = DEFAULT_SITE_URL,
) -> str:
    """Compose intro + ordered material/text blocks into email HTML (D-07)."""
    parts: list[str] = []
    intro_html = render_interstitial_html(intro)
    if intro_html:
        parts.append(intro_html)
    if not blocks:
        return "".join(parts)
    for block in blocks:
        kind = block.get("kind")
        if kind == "text":
            text_html = render_interstitial_html(str(block.get("text") or ""))
            if text_html:
                parts.append(text_html)
            continue
        if kind == "material":
            parts.append(
                render_material_email_block(
                    title=str(block.get("title") or ""),
                    dek=block.get("dek"),  # type: ignore[arg-type]
                    slug=str(block.get("slug") or ""),
                    site_url=site_url,
                )
            )
    return "".join(parts)
