"""ProfileRepository adapter — upsert/read public.profiles via injected client."""

from __future__ import annotations

import logging
from typing import Any, Protocol

from backend.domain.current_user import CurrentUser
from backend.domain.errors import PersistenceError
from backend.domain.recipient import Recipient, is_usable_email

_logger = logging.getLogger(__name__)

_DEFAULT_APP_ROLE = "employee"


class _SupabaseClient(Protocol):
    def table(self, name: str) -> Any: ...


def _row_to_user(row: dict[str, Any]) -> CurrentUser:
    raw_name = row.get("display_name")
    display_name = str(raw_name) if raw_name is not None and str(raw_name).strip() else None
    return CurrentUser(
        id=str(row["id"]),
        email=str(row["email"]),
        role=str(row.get("role") or _DEFAULT_APP_ROLE),
        display_name=display_name,
    )


class SupabaseProfileRepository:
    """Idempotent get_or_upsert against profiles (app_role), safe if Auth trigger exists."""

    def __init__(self, client: _SupabaseClient) -> None:
        self._client = client

    def get_or_upsert(self, user_id: str, email: str) -> CurrentUser:
        try:
            existing = (
                self._client.table("profiles")
                .select("id,email,role,display_name")
                .eq("id", user_id)
                .execute()
            )
            rows = getattr(existing, "data", None) or []
            if rows:
                return _row_to_user(rows[0])

            upserted = (
                self._client.table("profiles")
                .upsert(
                    {
                        "id": user_id,
                        "email": email,
                        "role": _DEFAULT_APP_ROLE,
                    }
                )
                .execute()
            )
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001 — map all SDK failures at boundary
            raise PersistenceError(f"profiles get_or_upsert failed: {exc}") from exc

        data = getattr(upserted, "data", None) or []
        if not data:
            raise PersistenceError("profiles upsert returned no rows")
        return _row_to_user(data[0])

    def set_display_name(self, user_id: str, display_name: str) -> CurrentUser:
        try:
            updated = (
                self._client.table("profiles")
                .update({"display_name": display_name})
                .eq("id", user_id)
                .execute()
            )
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001 — map all SDK failures at boundary
            raise PersistenceError(f"profiles set_display_name failed: {exc}") from exc

        data = getattr(updated, "data", None) or []
        if not data:
            raise PersistenceError("profiles set_display_name returned no rows")
        return _row_to_user(data[0])

    def list_digest_recipients(self) -> list[Recipient]:
        """All profiles with a usable email — no role filter (D-01), email-only (D-03).

        Runs on the service_role client wired by composition (RESEARCH Pitfall 7: the
        ``profiles_select_own`` RLS policy would hide every other row under a user JWT).
        Empty/malformed emails are excluded and logged; they never count toward M (D-02).

        WR-02: the select is paged with ``.range()`` until a short page is returned, so the
        PostgREST server-side ``max-rows`` cap can never silently truncate the audience
        (which would under-count planned M against D-01).
        """
        try:
            rows = self._list_all_profile_rows()
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001 — map all SDK failures at boundary
            raise PersistenceError(f"profiles list_digest_recipients failed: {exc}") from exc

        recipients: list[Recipient] = []
        for row in rows:
            email = str(row.get("email") or "")
            if not is_usable_email(email):
                _logger.info(
                    "digest audience: excluding profile id=%s email=%r (unusable)",
                    row.get("id"),
                    row.get("email"),
                )
                continue
            raw_name = row.get("display_name")
            display_name = (
                str(raw_name) if raw_name is not None and str(raw_name).strip() else None
            )
            recipients.append(Recipient(email=email, display_name=display_name))
        return recipients

    def _list_all_profile_rows(self) -> list[dict[str, Any]]:
        """Page the profiles select until a short page proves the audience is exhausted."""
        page_size = 1000
        rows: list[dict[str, Any]] = []
        start = 0
        while True:
            result = (
                self._client.table("profiles")
                .select("id,email,display_name")
                .range(start, start + page_size - 1)
                .execute()
            )
            page = list(getattr(result, "data", None) or [])
            rows.extend(page)
            if len(page) < page_size:
                break
            start += page_size
        return rows
