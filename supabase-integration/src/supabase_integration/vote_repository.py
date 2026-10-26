"""VoteRepository adapter — topics/tallies/votes via injected service_role client."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Protocol

from backend.domain.errors import PersistenceError, VoteConflictError
from backend.domain.vote import BallotTopic, PersonalVote


class _SupabaseClient(Protocol):
    def table(self, name: str) -> Any: ...


def _parse_dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    text = str(value).replace("Z", "+00:00")
    return datetime.fromisoformat(text)


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _row_to_personal(row: dict[str, Any]) -> PersonalVote:
    return PersonalVote(
        topic_id=str(row["topic_id"]),
        updated_at=_parse_dt(row["updated_at"]),
    )


def _db_id(value: str) -> int | str:
    return int(value) if str(value).isdigit() else value


def _rows(result: Any) -> list[Any]:
    return getattr(result, "data", None) or []


def _insert_vote(
    client: _SupabaseClient,
    *,
    cycle_id: str,
    user_id: str,
    topic_id: str,
    now_iso: str,
) -> PersonalVote:
    result = (
        client.table("votes")
        .insert(
            {
                "cycle_id": _db_id(cycle_id),
                "user_id": user_id,
                "topic_id": _db_id(topic_id),
                "updated_at": now_iso,
            }
        )
        .execute()
    )
    rows = _rows(result)
    if not rows:
        raise PersistenceError("votes insert returned no rows")
    return _row_to_personal(rows[0])


def _update_vote(
    client: _SupabaseClient,
    *,
    cycle_id: str,
    user_id: str,
    topic_id: str,
    now_iso: str,
    expected_updated_at: datetime,
) -> PersonalVote:
    expected_iso = _iso(expected_updated_at)
    payload = {"topic_id": _db_id(topic_id), "updated_at": now_iso}
    result = (
        client.table("votes")
        .update(payload)
        .eq("cycle_id", cycle_id)
        .eq("user_id", user_id)
        .eq("updated_at", expected_iso)
        .execute()
    )
    rows = _rows(result)
    if rows:
        return _row_to_personal(rows[0])

    # PostgREST may store timestamptz without Z — retry with fromisoformat form.
    alt_expected = expected_updated_at.astimezone(timezone.utc).isoformat()
    if alt_expected != expected_iso:
        result = (
            client.table("votes")
            .update(payload)
            .eq("cycle_id", cycle_id)
            .eq("user_id", user_id)
            .eq("updated_at", alt_expected)
            .execute()
        )
        rows = _rows(result)
    if not rows:
        raise VoteConflictError(cycle_id, user_id)
    return _row_to_personal(rows[0])


class SupabaseVoteRepository:
    """VoteRepository against topics / topic_materials / votes (service_role)."""

    def __init__(self, client: _SupabaseClient) -> None:
        self._client = client

    def list_topics_with_counts(self, cycle_id: str) -> list[BallotTopic]:
        try:
            topics_result = (
                self._client.table("topics")
                .select("id,cycle_id,name,description")
                .eq("cycle_id", cycle_id)
                .execute()
            )
            topics_rows = getattr(topics_result, "data", None) or []

            materials_result = self._client.table("topic_materials").select("topic_id").execute()
            materials_rows = getattr(materials_result, "data", None) or []

            votes_result = (
                self._client.table("votes")
                .select("topic_id")
                .eq("cycle_id", cycle_id)
                .execute()
            )
            votes_rows = getattr(votes_result, "data", None) or []
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001 — map SDK failures at boundary
            raise PersistenceError(f"votes list_topics failed: {exc}") from exc

        topic_ids = {str(row["id"]) for row in topics_rows}

        materials_count: dict[str, int] = {}
        for row in materials_rows:
            key = str(row["topic_id"])
            if key in topic_ids:
                materials_count[key] = materials_count.get(key, 0) + 1

        vote_count: dict[str, int] = {}
        for row in votes_rows:
            key = str(row["topic_id"])
            vote_count[key] = vote_count.get(key, 0) + 1

        topics: list[BallotTopic] = []
        for row in topics_rows:
            topic_id = str(row["id"])
            topics.append(
                BallotTopic(
                    id=topic_id,
                    title=str(row["name"]),
                    description=str(row.get("description") or ""),
                    materials_count=materials_count.get(topic_id, 0),
                    votes=vote_count.get(topic_id, 0),
                )
            )
        return topics

    def get_vote(self, cycle_id: str, user_id: str) -> PersonalVote | None:
        try:
            result = (
                self._client.table("votes")
                .select("topic_id,updated_at")
                .eq("cycle_id", cycle_id)
                .eq("user_id", user_id)
                .execute()
            )
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001 — map SDK failures at boundary
            raise PersistenceError(f"votes get failed: {exc}") from exc

        rows = getattr(result, "data", None) or []
        if not rows:
            return None
        return _row_to_personal(rows[0])

    def upsert_vote(
        self,
        *,
        cycle_id: str,
        user_id: str,
        topic_id: str,
        expected_updated_at: datetime | None,
    ) -> PersonalVote:
        now = datetime.now(timezone.utc)
        now_iso = _iso(now)
        try:
            if expected_updated_at is None:
                return _insert_vote(
                    self._client,
                    cycle_id=cycle_id,
                    user_id=user_id,
                    topic_id=topic_id,
                    now_iso=now_iso,
                )
            return _update_vote(
                self._client,
                cycle_id=cycle_id,
                user_id=user_id,
                topic_id=topic_id,
                now_iso=now_iso,
                expected_updated_at=expected_updated_at,
            )
        except VoteConflictError:
            raise
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001 — map SDK failures at boundary
            message = str(exc).lower()
            if "duplicate" in message or "unique" in message:
                raise VoteConflictError(cycle_id, user_id) from exc
            raise PersistenceError(f"votes upsert failed: {exc}") from exc
