"""RED→GREEN: the `## Аудитория` prompt scaffolding must not leak into the body.

`lecture.md` / `podcast.md` end with a `## Аудитория` section whose text is an
instruction ("Кто целевая аудитория материала? Верни JSON array ролей из: ...").
The role contract is the separate JSON `roles` key, so that section is prompt
scaffolding — not article content. Real models sometimes still emit it inside
`body_markdown`, either as the raw answer or by echoing the instruction verbatim
(observed live on materials 9/11 as JSON, and 12 as the echoed prompt). The
draft must normalise it away so the reader body stays clean.
"""

from __future__ import annotations

PROMPT_LINE = "Кто целевая аудитория материала? Верни JSON array ролей из: employee, analyst, ds."


def _draft(body_markdown: str, roles=None):
    from data_collection.dto.article_draft import ArticleDraft

    payload = {"title": "t", "dek": "d", "body_markdown": body_markdown}
    if roles is not None:
        payload["roles"] = roles
    return ArticleDraft.model_validate(payload)


def test_body_strips_trailing_audience_section_holding_role_json() -> None:
    body = '## Тезис\n\nМысль.\n\n## Аудитория\n\n["employee", "analyst", "ds"]'

    draft = _draft(body)

    assert "Аудитория" not in draft.body_markdown
    assert '["employee"' not in draft.body_markdown
    assert draft.body_markdown == "## Тезис\n\nМысль."


def test_body_strips_audience_section_when_model_echoes_the_prompt() -> None:
    body = f"## Тезис\n\nМысль.\n\n## Аудитория\n\n{PROMPT_LINE}"

    draft = _draft(body)

    assert "Аудитория" not in draft.body_markdown
    assert "Кто целевая аудитория" not in draft.body_markdown
    assert draft.body_markdown == "## Тезис\n\nМысль."


def test_body_without_audience_section_is_unchanged() -> None:
    body = "## Тезис\n\nМысль.\n\n## Вывод\n\nИтог."

    draft = _draft(body)

    assert draft.body_markdown == body


def test_body_keeps_a_later_section_that_follows_the_audience_block() -> None:
    body = (
        "## Тезис\n\nМысль.\n\n## Аудитория\n\n"
        '["ds"]\n\n## Приложение\n\nПрочее.'
    )

    draft = _draft(body)

    assert "Аудитория" not in draft.body_markdown
    assert draft.body_markdown == "## Тезис\n\nМысль.\n\n## Приложение\n\nПрочее."


def test_body_mention_of_audience_mid_text_is_preserved() -> None:
    """Only the scaffolding heading triggers removal, not the word itself."""
    body = "## Тезис\n\nАудитория СВА — аналитики. Материал им полезен."

    draft = _draft(body)

    assert draft.body_markdown == body


def test_audience_stripping_is_idempotent() -> None:
    body = f"## Тезис\n\nМысль.\n\n## Аудитория\n\n{PROMPT_LINE}"

    once = _draft(body).body_markdown
    twice = _draft(once).body_markdown

    assert once == twice


def test_roles_key_still_wins_when_body_also_carries_the_section() -> None:
    body = f"## Тезис\n\nМысль.\n\n## Аудитория\n\n{PROMPT_LINE}"

    draft = _draft(body, roles=["analyst"])

    assert draft.roles == ["analyst"]
    assert "Аудитория" not in draft.body_markdown
