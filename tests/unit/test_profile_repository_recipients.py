"""D-01/D-02/D-03 recipients unit tests — in-memory audience honesty (MAIL-03).

Plan 01 added ``ProfileRepository.list_digest_recipients`` + the in-memory fake; this file
pins the audience contract: all roles with a usable ``profiles.email``, empty/malformed
excluded and logged, ``profiles.email``-only address source.
"""

from __future__ import annotations

import logging

from backend.domain.current_user import CurrentUser
from backend.domain.recipient import Recipient
from backend.tests_support.in_memory import InMemoryProfileRepository


def _seed(
    repo: InMemoryProfileRepository,
    *,
    user_id: str,
    email: str,
    role: str = "employee",
    display_name: str | None = None,
) -> None:
    repo._by_id[user_id] = CurrentUser(
        id=user_id,
        email=email,
        role=role,
        display_name=display_name,
    )


def test_list_digest_recipients_includes_every_role_with_usable_email() -> None:
    """D-01: no role filter, no admin exclusion — every usable profile is an addressee."""
    repo = InMemoryProfileRepository()
    _seed(repo, user_id="admin-1", email="admin@sberbank.ru", role="admin")
    _seed(repo, user_id="emp-1", email="emp@sberbank.ru", role="employee")
    _seed(repo, user_id="analyst-1", email="analyst@omega.sbrf.ru", role="analyst")

    recipients = list(repo.list_digest_recipients())

    assert all(isinstance(r, Recipient) for r in recipients)
    assert {r.email for r in recipients} == {
        "admin@sberbank.ru",
        "emp@sberbank.ru",
        "analyst@omega.sbrf.ru",
    }


def test_list_digest_recipients_excludes_empty_and_malformed_emails(caplog) -> None:
    """D-02: unusable emails never count toward M and are logged (who/why)."""
    repo = InMemoryProfileRepository()
    _seed(repo, user_id="good", email="good@sberbank.ru")
    _seed(repo, user_id="empty", email="")
    _seed(repo, user_id="blank", email="   ")
    _seed(repo, user_id="no-at", email="not-an-email")
    _seed(repo, user_id="no-local", email="@sberbank.ru")
    _seed(repo, user_id="no-domain", email="user@")

    with caplog.at_level(logging.INFO):
        recipients = list(repo.list_digest_recipients())

    assert [r.email for r in recipients] == ["good@sberbank.ru"]
    excluded_log = " ".join(record.getMessage() for record in caplog.records)
    assert "empty" in excluded_log
    assert "no-domain" in excluded_log


def test_list_digest_recipients_uses_profiles_email_only() -> None:
    """D-03: the send address is ``profiles.email``; display_name is metadata only."""
    repo = InMemoryProfileRepository()
    _seed(repo, user_id="u", email="real@sberbank.ru", display_name="Реальное имя")

    (recipient,) = list(repo.list_digest_recipients())

    assert recipient.email == "real@sberbank.ru"
    assert recipient.display_name == "Реальное имя"
