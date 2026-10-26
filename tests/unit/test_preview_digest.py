"""preview_digest_email — approved∩ready preview DTO (ADMIN-04, D-86, G-05-1)."""

from __future__ import annotations

from datetime import date

import pytest

from backend.application.use_cases.preview_digest_email import (
    PreviewMaterialBlock,
    PreviewTextBlock,
    preview_digest_email,
)
from backend.domain.errors import EmptySendPoolError, InvalidPreviewCompositionError
from backend.domain.shortlist import ShortlistBatch, ShortlistItem
from backend.tests_support.in_memory import (
    InMemoryProfileRepository,
    InMemoryShortlistRepository,
)


def _item(
    *,
    material_id: int,
    rank: int,
    title: str,
    material_status: str,
    decision: str,
    dek: str | None = None,
    slug: str | None = None,
) -> ShortlistItem:
    return ShortlistItem(
        material_id=material_id,
        rank=rank,
        title=title,
        material_status=material_status,
        decision=decision,
        score=0.5,
        score_factors={"factors": [{"label": "A"}, {"label": "B"}]},
        dek=dek,
        slug=slug,
    )


def _batch(*items: ShortlistItem) -> ShortlistBatch:
    return ShortlistBatch(
        id=42,
        week_start=date(2026, 9, 15),
        sent_at=None,
        items=items,
    )


def test_preview_lists_only_approved_ready_items() -> None:
    """ADMIN-04 / D-83 / D-86: preview items = approved ∩ ready only."""
    repo = InMemoryShortlistRepository(
        batch=_batch(
            _item(
                material_id=101,
                rank=1,
                title="Ready approved",
                material_status="ready",
                decision="approved",
            ),
            _item(
                material_id=102,
                rank=2,
                title="Draft approved",
                material_status="draft",
                decision="approved",
            ),
            _item(
                material_id=103,
                rank=3,
                title="Ready pending",
                material_status="ready",
                decision="pending",
            ),
            _item(
                material_id=104,
                rank=4,
                title="Ready rejected",
                material_status="ready",
                decision="rejected",
            ),
        )
    )

    preview = preview_digest_email(repo)

    assert [item.material_id for item in preview.items] == [101]
    assert preview.items[0].title == "Ready approved"
    assert preview.subject
    assert preview.body
    assert repo.get_current_batch() is not None
    assert repo.get_current_batch().sent_at is None


def test_preview_empty_approved_ready_raises() -> None:
    """ADMIN-04 / ADMIN-07 empty probe: no approved∩ready → EmptySendPoolError."""
    repo = InMemoryShortlistRepository(
        batch=_batch(
            _item(
                material_id=102,
                rank=1,
                title="Draft approved",
                material_status="draft",
                decision="approved",
            ),
            _item(
                material_id=103,
                rank=2,
                title="Ready pending",
                material_status="ready",
                decision="pending",
            ),
        )
    )

    with pytest.raises(EmptySendPoolError):
        preview_digest_email(repo)

    assert repo.get_current_batch().sent_at is None


def test_preview_no_batch_raises_empty_pool() -> None:
    repo = InMemoryShortlistRepository(batch=None)

    with pytest.raises(EmptySendPoolError):
        preview_digest_email(repo)


def test_preview_composes_intro_and_ordered_blocks() -> None:
    """G-05-1 / ADMIN-04: intro + material/text blocks appear in body order."""
    repo = InMemoryShortlistRepository(
        batch=_batch(
            _item(
                material_id=201,
                rank=1,
                title="Title A",
                material_status="ready",
                decision="approved",
            ),
            _item(
                material_id=202,
                rank=2,
                title="Title B",
                material_status="ready",
                decision="approved",
            ),
        )
    )

    preview = preview_digest_email(
        repo,
        intro="Добрый день коллеги!",
        blocks=(
            PreviewMaterialBlock(material_id=201),
            PreviewTextBlock(text="связка"),
            PreviewMaterialBlock(material_id=202),
        ),
    )

    assert "Добрый день коллеги!" in preview.body
    intro_at = preview.body.index("Добрый день коллеги!")
    a_at = preview.body.index("Title A")
    bridge_at = preview.body.index("связка")
    b_at = preview.body.index("Title B")
    assert intro_at < a_at < bridge_at < b_at
    assert [item.material_id for item in preview.items] == [201, 202]
    assert [item.rank for item in preview.items] == [1, 2]
    assert repo.get_current_batch().sent_at is None


def test_preview_empty_intro_omits_intro_paragraph() -> None:
    repo = InMemoryShortlistRepository(
        batch=_batch(
            _item(
                material_id=201,
                rank=1,
                title="Only title",
                material_status="ready",
                decision="approved",
            ),
        )
    )

    preview = preview_digest_email(repo, intro="", blocks=None)

    assert "Добрый день" not in preview.body
    assert "Only title" in preview.body
    assert [item.material_id for item in preview.items] == [201]


def test_preview_default_blocks_use_approved_ready_by_rank() -> None:
    """Backward-compatible ADMIN-04 pool when blocks omitted."""
    repo = InMemoryShortlistRepository(
        batch=_batch(
            _item(
                material_id=202,
                rank=2,
                title="Second",
                material_status="ready",
                decision="approved",
            ),
            _item(
                material_id=201,
                rank=1,
                title="First",
                material_status="ready",
                decision="approved",
            ),
        )
    )

    preview = preview_digest_email(repo)

    assert [item.material_id for item in preview.items] == [201, 202]
    assert preview.body.index("First") < preview.body.index("Second")


def test_preview_material_outside_pool_raises_invalid_composition() -> None:
    repo = InMemoryShortlistRepository(
        batch=_batch(
            _item(
                material_id=201,
                rank=1,
                title="Ready approved",
                material_status="ready",
                decision="approved",
            ),
            _item(
                material_id=202,
                rank=2,
                title="Ready pending",
                material_status="ready",
                decision="pending",
            ),
        )
    )

    with pytest.raises(InvalidPreviewCompositionError):
        preview_digest_email(
            repo,
            intro="",
            blocks=(PreviewMaterialBlock(material_id=202),),
        )

    assert repo.get_current_batch().sent_at is None


def test_preview_html_present_with_interstitial_paragraphs() -> None:
    """ADUX-02/D-10: additive html; ADUX-03/D-13: interstitial \\n\\n → <p> tags."""
    repo = InMemoryShortlistRepository(
        batch=_batch(
            _item(
                material_id=301,
                rank=1,
                title="HTML Title",
                material_status="ready",
                decision="approved",
                dek="HTML dek",
                slug="html-title",
            ),
        )
    )

    preview = preview_digest_email(
        repo,
        intro="Para one\n\nPara two",
        blocks=(
            PreviewMaterialBlock(material_id=301),
            PreviewTextBlock(text="Bridge A\n\nBridge B"),
        ),
        site_url="http://127.0.0.1:5173",
    )

    assert isinstance(preview.html, str)
    assert preview.html
    assert "<p>Para one</p><p>Para two</p>" in preview.html
    assert "<p>Bridge A</p><p>Bridge B</p>" in preview.html
    assert "HTML Title" in preview.html
    assert 'href="http://127.0.0.1:5173/materials/html-title"' in preview.html
    assert "Читать →" in preview.html
    assert "/issues/" not in preview.html


def test_preview_plain_preserves_internal_blank_lines() -> None:
    """ADUX-03/D-14: plain body keeps internal \\n\\n after outer strip."""
    repo = InMemoryShortlistRepository(
        batch=_batch(
            _item(
                material_id=302,
                rank=1,
                title="Plain Mat",
                material_status="ready",
                decision="approved",
                slug="plain-mat",
            ),
        )
    )

    preview = preview_digest_email(
        repo,
        intro="  Intro A\n\nIntro B  ",
        blocks=(
            PreviewTextBlock(text="  Mid A\n\nMid B  "),
            PreviewMaterialBlock(material_id=302),
        ),
    )

    assert "Intro A\n\nIntro B" in preview.body
    assert "Mid A\n\nMid B" in preview.body


def test_preview_plain_material_includes_dek_and_absolute_url() -> None:
    """RESEARCH Q3: plain material segments = title + optional dek + absolute URL."""
    repo = InMemoryShortlistRepository(
        batch=_batch(
            _item(
                material_id=303,
                rank=1,
                title="Enriched",
                material_status="ready",
                decision="approved",
                dek="A dek line",
                slug="enriched",
            ),
        )
    )

    preview = preview_digest_email(
        repo,
        site_url="http://127.0.0.1:5173",
    )

    assert "Enriched" in preview.body
    assert "A dek line" in preview.body
    assert "http://127.0.0.1:5173/materials/enriched" in preview.body


def test_settings_site_url_from_site_url_then_public_then_default() -> None:
    """D-11 / RESEARCH Q2: SITE_URL → PUBLIC_SITE_URL → default."""
    from backend.composition.settings import Settings

    assert Settings.from_env({}).site_url == "http://127.0.0.1:5173"
    assert (
        Settings.from_env({"PUBLIC_SITE_URL": "http://public.example"}).site_url
        == "http://public.example"
    )
    assert (
        Settings.from_env(
            {
                "SITE_URL": "http://primary.example",
                "PUBLIC_SITE_URL": "http://public.example",
            }
        ).site_url
        == "http://primary.example"
    )


def _parity_composition_fixture(*, with_dek: bool):
    """Shared intro/blocks/batch for preview≡send HTML parity (D-12)."""
    from datetime import datetime, timezone

    from backend.infrastructure.stub_mailer import StubMailer
    from backend.tests_support.in_memory import (
        InMemoryDigestPublisher,
        InMemoryIssueRepository,
        InMemoryPingRecorder,
    )

    dek = "Parity dek with detail" if with_dek else None
    batch = _batch(
        _item(
            material_id=401,
            rank=1,
            title="Parity Material",
            material_status="ready",
            decision="approved",
            dek=dek,
            slug="parity-material",
        ),
        _item(
            material_id=402,
            rank=2,
            title="Second Parity",
            material_status="ready",
            decision="approved",
            slug="second-parity",
        ),
    )
    intro = "Intro A\n\nIntro B"
    blocks = (
        PreviewMaterialBlock(material_id=401),
        PreviewTextBlock(text="Bridge\n\nLine"),
        PreviewMaterialBlock(material_id=402),
    )
    site_url = "https://parity.example"
    repo = InMemoryShortlistRepository(batch=batch)
    return {
        "repo": repo,
        "intro": intro,
        "blocks": blocks,
        "site_url": site_url,
        "mailer": StubMailer(),
        "publisher": InMemoryDigestPublisher(
            lambda: repo,
            lambda: InMemoryIssueRepository(),
        ),
        "pings": InMemoryPingRecorder(),
        "profiles": InMemoryProfileRepository(),
        "now": datetime(2026, 9, 21, 15, 0, tzinfo=timezone.utc),
    }


def test_preview_email_html_matches_send_html() -> None:
    """ADUX-02 / D-12: same intro/blocks → preview.html == send body_html."""
    from backend.application.use_cases.send_digest import send_digest

    for with_dek in (True, False):
        fx = _parity_composition_fixture(with_dek=with_dek)
        preview = preview_digest_email(
            fx["repo"],
            intro=fx["intro"],
            blocks=fx["blocks"],
            site_url=fx["site_url"],
        )
        # Fresh batch for send — preview must not mark sent; use same fixture clone.
        fx_send = _parity_composition_fixture(with_dek=with_dek)
        send_digest(
            fx_send["repo"],
            fx_send["publisher"],
            fx_send["mailer"],
            fx_send["pings"],
            fx_send["profiles"],
            actor_user_id="admin-uuid-1",
            now=fx_send["now"],
            intro=fx_send["intro"],
            blocks=fx_send["blocks"],
            site_url=fx_send["site_url"],
        )
        send_html = fx_send["mailer"].last_body_html
        assert isinstance(send_html, str)
        assert send_html == preview.html
        assert "/issues/" not in send_html
        assert "Intro A" in send_html
        assert "Bridge" in send_html
        if with_dek:
            assert "Parity dek with detail" in send_html
        else:
            assert "Parity dek with detail" not in send_html

