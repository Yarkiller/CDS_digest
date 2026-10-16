"""Profile persistence port — upsert on first authenticated /me."""

from __future__ import annotations

from typing import Protocol, Sequence

from backend.domain.current_user import CurrentUser
from backend.domain.recipient import Recipient


class ProfileRepository(Protocol):
    def get_or_upsert(self, user_id: str, email: str) -> CurrentUser: ...

    def set_display_name(self, user_id: str, display_name: str) -> CurrentUser: ...

    def list_digest_recipients(self) -> Sequence[Recipient]:
        """All profiles with a usable email — no role filter, no admin exclusion (D-01).

        Empty/malformed emails are excluded and logged, never counted toward M (D-02).
        """
        ...
