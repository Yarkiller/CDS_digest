"""email_render + email_chrome — interstitial HTML matrix and ban asserts (ADUX-02/03/04).

Closed ban tokens (D-18): test-header, test_header, testheader — assert-only (D-17/D-19).
"""

from __future__ import annotations

from backend.application.use_cases.email_render import (
    render_email_html,
    render_interstitial_html,
    render_material_email_block,
)
from backend.domain.email_chrome import FORBIDDEN_LOWER, contains_forbidden_chrome


def test_render_interstitial_html_empty_returns_empty() -> None:
    assert render_interstitial_html("") == ""


def test_render_interstitial_html_whitespace_only_returns_empty() -> None:
    assert render_interstitial_html("   \n\t  ") == ""


def test_render_interstitial_html_single_paragraph() -> None:
    assert render_interstitial_html("hello") == "<p>hello</p>"


def test_render_interstitial_html_two_paragraphs_via_blank_line() -> None:
    assert render_interstitial_html("one\n\ntwo") == "<p>one</p><p>two</p>"


def test_render_interstitial_html_single_newline_becomes_br() -> None:
    assert render_interstitial_html("a\nb") == "<p>a<br>b</p>"


def test_render_interstitial_html_strips_leading_trailing_whitespace() -> None:
    assert render_interstitial_html("  padded  ") == "<p>padded</p>"


def test_render_interstitial_html_escapes_angle_brackets_and_quotes() -> None:
    out = render_interstitial_html('<tag attr="x">')
    assert "<tag" not in out
    assert "&lt;tag" in out
    assert "&quot;x&quot;" in out
    assert out.startswith("<p>") and out.endswith("</p>")


def test_render_material_email_block_title_dek_and_read_link() -> None:
    html = render_material_email_block(
        title="My Title",
        dek="Short dek",
        slug="my-slug",
        site_url="http://127.0.0.1:5173",
    )
    assert "My Title" in html
    assert "Short dek" in html
    assert 'href="http://127.0.0.1:5173/materials/my-slug"' in html
    assert "Читать →" in html
    assert "/issues/" not in html


def test_render_material_email_block_omits_empty_dek() -> None:
    html = render_material_email_block(
        title="Only title",
        dek="  ",
        slug="only",
        site_url="http://example.test",
    )
    assert "Only title" in html
    assert html.count("<p>") == 1  # link paragraph only
    assert "Читать →" in html


def test_render_material_email_block_defaults_site_url() -> None:
    html = render_material_email_block(title="T", dek=None, slug="s")
    assert 'href="http://127.0.0.1:5173/materials/s"' in html


def test_render_material_email_block_escapes_title_and_dek() -> None:
    html = render_material_email_block(
        title="<bad>",
        dek='x"y',
        slug="safe",
        site_url="http://127.0.0.1:5173",
    )
    assert "<bad>" not in html
    assert "&lt;bad&gt;" in html
    assert "&quot;y" in html or "&#x27;" in html or "&quot;" in html


def test_render_material_email_block_omits_read_link_when_slug_blank() -> None:
    """W-2: a blank slug must not emit a dead `/materials/` link (ADUX-02 honesty)."""
    html = render_material_email_block(
        title="No Slug",
        dek="Kept dek",
        slug="",
        site_url="http://127.0.0.1:5173",
    )
    assert "No Slug" in html
    assert "Kept dek" in html
    assert "Читать →" not in html
    assert "/materials/" not in html


def test_render_material_email_block_omits_read_link_when_slug_whitespace() -> None:
    """W-2: whitespace-only slug is blank too — no dead link."""
    html = render_material_email_block(
        title="Only Title",
        dek=None,
        slug="   ",
        site_url="http://example.test",
    )
    assert "Only Title" in html
    assert "Читать →" not in html
    assert "/materials/" not in html


def test_render_email_html_omits_read_link_for_blank_slug_material_block() -> None:
    """W-2: block-level path (render_email_html) also skips the reader link for a blank slug."""
    html = render_email_html(
        intro="",
        blocks=({"kind": "material", "title": "Blank Slug", "dek": None, "slug": ""},),
        site_url="http://127.0.0.1:5173",
    )
    assert "Blank Slug" in html
    assert "Читать →" not in html
    assert "/materials/" not in html


def test_render_email_html_applies_interstitial_to_intro_and_includes_material() -> None:
    html = render_email_html(
        intro="Intro para one\n\nIntro para two",
        blocks=(
            {"kind": "material", "title": "Seeded", "dek": "Dek", "slug": "seeded"},
            {"kind": "text", "text": "Bridge\n\nMore"},
        ),
        site_url="http://127.0.0.1:5173",
    )
    assert "<p>Intro para one</p><p>Intro para two</p>" in html
    assert "Seeded" in html
    assert 'href="http://127.0.0.1:5173/materials/seeded"' in html
    assert "Читать →" in html
    assert "<p>Bridge</p><p>More</p>" in html
    assert "/issues/" not in html


def test_render_email_html_defaults_site_url() -> None:
    html = render_email_html(
        intro="",
        blocks=({"kind": "material", "title": "T", "dek": None, "slug": "x"},),
    )
    assert 'href="http://127.0.0.1:5173/materials/x"' in html


def test_render_material_email_block_read_link_opens_in_new_context() -> None:
    """D-11: the CTA escapes the sandboxed preview via target=_blank + rel=noopener noreferrer."""
    html = render_material_email_block(
        title="My Title",
        dek="Short dek",
        slug="my-slug",
        site_url="http://127.0.0.1:5173",
    )
    assert 'target="_blank"' in html
    assert 'rel="noopener noreferrer"' in html
    # D-11: the href stays reader-facing — preview and the real send share this builder.
    assert 'href="http://127.0.0.1:5173/materials/my-slug"' in html


def test_render_email_html_material_link_opens_in_new_context() -> None:
    """D-11: the block-level path carries the same anchor attributes as the block helper."""
    html = render_email_html(
        intro="",
        blocks=({"kind": "material", "title": "Seeded", "dek": None, "slug": "seeded"},),
        site_url="http://127.0.0.1:5173",
    )
    assert 'target="_blank"' in html
    assert 'rel="noopener noreferrer"' in html
    assert 'href="http://127.0.0.1:5173/materials/seeded"' in html


def test_render_material_email_block_is_idempotent() -> None:
    """D-11: the added attributes are static literals — rendering twice is byte-identical."""
    first = render_material_email_block(
        title="Same",
        dek="Same dek",
        slug="same-slug",
        site_url="http://127.0.0.1:5173",
    )
    second = render_material_email_block(
        title="Same",
        dek="Same dek",
        slug="same-slug",
        site_url="http://127.0.0.1:5173",
    )
    assert first == second
    blocks = ({"kind": "material", "title": "Same", "dek": None, "slug": "same-slug"},)
    assert render_email_html(intro="", blocks=blocks) == render_email_html(
        intro="", blocks=blocks
    )


def test_render_material_email_block_blank_slug_emits_no_anchor_attributes() -> None:
    """W-2 preserved: a blank slug emits no anchor, so target/rel cannot sit on a dead link."""
    for blank in ("", "   "):
        html = render_material_email_block(
            title="Blank",
            dek=None,
            slug=blank,
            site_url="http://127.0.0.1:5173",
        )
        assert "Читать →" not in html
        assert "/materials/" not in html
        assert "target=" not in html
        assert "rel=" not in html


def test_forbidden_lower_closed_list() -> None:
    assert FORBIDDEN_LOWER == ["test-header", "test_header", "testheader"]


def test_contains_forbidden_chrome_detects_hyphen_underscore_concat_case_insensitive() -> None:
    assert contains_forbidden_chrome("prefix TEST-HEADER suffix")
    assert contains_forbidden_chrome("xx Test_Header yy")
    assert contains_forbidden_chrome("testHeader")
    assert not contains_forbidden_chrome("clean editorial copy")


def test_clean_render_email_html_fixture_has_no_forbidden_chrome() -> None:
    html = render_email_html(
        intro="Weekly note",
        blocks=(
            {
                "kind": "material",
                "title": "Clean Title",
                "dek": "Clean dek",
                "slug": "clean-title",
            },
        ),
        site_url="http://127.0.0.1:5173",
    )
    assert not contains_forbidden_chrome(html)


def test_email_render_module_does_not_import_or_call_ban_helper() -> None:
    """D-17: renderers must not filter via contains_forbidden_chrome (assert-only)."""
    from pathlib import Path

    src = Path(render_email_html.__code__.co_filename).read_text(encoding="utf-8")
    assert "email_chrome" not in src
    assert "contains_forbidden_chrome" not in src
    assert "FORBIDDEN_LOWER" not in src


def test_python_forbidden_lower_matches_js_mirror() -> None:
    """D-18: Python FORBIDDEN_LOWER must equal web/src/utils/forbiddenChrome.js list order/values."""
    import ast
    import re
    from pathlib import Path

    js_path = (
        Path(__file__).resolve().parents[2] / "web" / "src" / "utils" / "forbiddenChrome.js"
    )
    assert js_path.is_file(), f"missing JS ban mirror: {js_path}"
    js_src = js_path.read_text(encoding="utf-8")
    match = re.search(
        r"export\s+const\s+FORBIDDEN_LOWER\s*=\s*(\[[^\]]*\])",
        js_src,
        flags=re.DOTALL,
    )
    assert match is not None, "FORBIDDEN_LOWER export not found in forbiddenChrome.js"
    js_list = ast.literal_eval(match.group(1))
    assert js_list == FORBIDDEN_LOWER
    assert "containsForbiddenChrome" in js_src
