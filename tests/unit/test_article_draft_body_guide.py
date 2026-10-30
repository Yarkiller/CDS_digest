"""RED→GREEN: the `## Гайд` extras furniture must not leak into the pass-1 body.

Pass-1 never owns a guide heading (KIND-03, D-09…D-12). Models still leak an empty
or filled `## Гайд` section, plus the honest-absence substring «ссылки скоро появятся».
The draft must sanitise both so persist never stores extras furniture. The strip is
a sibling of `## Аудитория`: it never raises, and real talk headings stay.
"""

from __future__ import annotations

PLACEHOLDER = "ссылки скоро появятся"


def _draft(body_markdown: str, roles=None, topic_kind=None):
    from data_collection.dto.article_draft import ArticleDraft

    payload = {"title": "t", "dek": "d", "body_markdown": body_markdown}
    if roles is not None:
        payload["roles"] = roles
    if topic_kind is not None:
        payload["topic_kind"] = topic_kind
    return ArticleDraft.model_validate(payload)


def test_body_strips_trailing_empty_guide_section() -> None:
    body = "## Тезис\n\nМысль.\n\n## Гайд\n"

    draft = _draft(body)

    assert "Гайд" not in draft.body_markdown
    assert draft.body_markdown == "## Тезис\n\nМысль."


def test_body_strips_filled_guide_section() -> None:
    """D-10: extras exist only in pass-2 — a filled Гайд still goes."""
    body = "## Тезис\n\nМысль.\n\n## Гайд\n\n1. Open SAP\n2. Click Export"

    draft = _draft(body)

    assert "Гайд" not in draft.body_markdown
    assert "Open SAP" not in draft.body_markdown
    assert draft.body_markdown == "## Тезис\n\nМысль."


def test_body_keeps_a_later_section_that_follows_the_guide_block() -> None:
    body = (
        "## Тезис\n\nМысль.\n\n## Гайд\n\n1. Open SAP\n\n## Конкретика\n\nФакты."
    )

    draft = _draft(body)

    assert "Гайд" not in draft.body_markdown
    assert "Open SAP" not in draft.body_markdown
    assert draft.body_markdown == "## Тезис\n\nМысль.\n\n## Конкретика\n\nФакты."


def test_body_mention_of_guide_mid_text_is_preserved() -> None:
    """Only the scaffolding heading triggers removal, not the in-prose word."""
    body = "## Тезис\n\nПрактический гайд на VPS. Материал им полезен."

    draft = _draft(body)

    assert draft.body_markdown == body
    assert "гайд" in draft.body_markdown


def test_d12_talk_headings_are_kept() -> None:
    """D-12: exact Гайд only — English/other how-to titles are real talk content."""
    body = (
        "## Guide\n\nKeep.\n\n"
        "## How-to\n\nKeep.\n\n"
        "## Как сделать\n\nKeep.\n\n"
        "## Tutorial\n\nKeep.\n\n"
        "## Шпаргалка\n\nKeep."
    )

    draft = _draft(body)

    assert draft.body_markdown == body
    assert "## Guide" in draft.body_markdown
    assert "## How-to" in draft.body_markdown
    assert "## Как сделать" in draft.body_markdown
    assert "## Tutorial" in draft.body_markdown
    assert "## Шпаргалка" in draft.body_markdown


def test_body_strips_placeholder_substring_outside_the_guide_section() -> None:
    """D-10: the exact honest-absence copy is deleted even when it is not under Гайд."""
    body = f"## Тезис\n\nМысль.\n\n{PLACEHOLDER}"

    draft = _draft(body)

    assert PLACEHOLDER not in draft.body_markdown
    assert draft.body_markdown == "## Тезис\n\nМысль."


def test_body_strips_lowercase_atx_guide_heading() -> None:
    """RESEARCH A3: re.IGNORECASE on Cyrillic Гайд matches a leaked ## гайд."""
    body = "## Тезис\n\nМысль.\n\n## гайд\n\n1. Open SAP"

    draft = _draft(body)

    assert "гайд" not in draft.body_markdown
    assert "Гайд" not in draft.body_markdown
    assert "Open SAP" not in draft.body_markdown
    assert draft.body_markdown == "## Тезис\n\nМысль."


def test_practical_draft_also_loses_guide_section() -> None:
    """D-11: the strip runs on every pass-1 body, including practical stamps."""
    body = "## Тезис\n\nМысль.\n\n## Гайд\n\n1. Open SAP"

    draft = _draft(body, topic_kind="practical")

    assert draft.topic_kind == "practical"
    assert "Гайд" not in draft.body_markdown
    assert draft.body_markdown == "## Тезис\n\nМысль."


def test_guide_stripping_is_idempotent() -> None:
    body = f"## Тезис\n\nМысль.\n\n## Гайд\n\n1. Open SAP\n\n{PLACEHOLDER}"

    once = _draft(body).body_markdown
    twice = _draft(once).body_markdown

    assert once == twice
    assert "Гайд" not in once
    assert PLACEHOLDER not in once


def test_body_strips_every_guide_section_not_only_the_first() -> None:
    """KIND-03: a later ## Гайд is furniture too — the first-match terminator must not keep it."""
    body = (
        "## Тезис\n\nМысль.\n\n"
        "## Гайд\n\nfirst leak\n\n"
        "## Гайд\n\nsecond leak"
    )

    draft = _draft(body)

    assert "Гайд" not in draft.body_markdown
    assert "first leak" not in draft.body_markdown
    assert "second leak" not in draft.body_markdown
    assert draft.body_markdown == "## Тезис\n\nМысль."


def test_body_that_is_only_a_guide_section_still_validates_without_guide() -> None:
    """KIND-03: leaked furniture is deleted, not rejected; an emptied body keeps a stub."""
    body = "## Гайд\n\n1. Open SAP"

    draft = _draft(body)

    assert "Гайд" not in draft.body_markdown
    assert "Open SAP" not in draft.body_markdown
    assert draft.body_markdown.strip() != ""
