"""Corporate email domain allowlist — ADR-0003 / D-04 / AUTH-01."""

from __future__ import annotations

import ast
from pathlib import Path

from backend.domain.auth_email import DEFAULT_ALLOWED_EMAIL_DOMAINS, is_allowed_corporate_email


def test_allowed_sberbank_and_omega_domains_case_insensitive() -> None:
    assert is_allowed_corporate_email("user@sberbank.ru") is True
    assert is_allowed_corporate_email("User@Omega.Sbrf.Ru") is True
    assert is_allowed_corporate_email("a@SBERBANK.RU") is True


def test_disallowed_and_malformed_emails_return_false() -> None:
    assert is_allowed_corporate_email("user@gmail.com") is False
    assert is_allowed_corporate_email("user@sberbank.ru.com") is False
    assert is_allowed_corporate_email("") is False
    assert is_allowed_corporate_email("not-an-email") is False
    assert is_allowed_corporate_email("@sberbank.ru") is False
    assert is_allowed_corporate_email("user@") is False


def test_custom_allowed_domains_override_defaults() -> None:
    assert is_allowed_corporate_email("a@example.com", allowed_domains=("@example.com",)) is True
    assert is_allowed_corporate_email("a@sberbank.ru", allowed_domains=("@example.com",)) is False


def test_default_domains_match_adr_0003() -> None:
    assert DEFAULT_ALLOWED_EMAIL_DOMAINS == ("@sberbank.ru", "@omega.sbrf.ru")


def test_domain_module_has_no_http_or_sdk_imports() -> None:
    path = Path("backend/src/backend/domain/auth_email.py")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    forbidden = {"fastapi", "httpx", "supabase", "jwt", "requests"}
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported.isdisjoint(forbidden)
