from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass, field, replace
from datetime import datetime, time, timezone
from typing import Any

from backend.application.ports.digest_publisher import DigestPublication
from backend.domain.current_user import CurrentUser
from backend.domain.errors import (
    AlreadySentError,
    EmptySendPoolError,
    ShortlistNotFoundError,
    VoteConflictError,
)
from backend.domain.recipient import Recipient, is_usable_email
from backend.domain.issue import Issue, IssueItem
from backend.domain.knowledge import KnowledgeChunk, KnowledgeHit
from backend.domain.material import Material, MaterialStatus
from backend.domain.ingest_source import IngestSource
from backend.domain.ingestion_schedule import (
    IngestionSchedule,
    default_ingestion_schedule,
)
from backend.domain.pipeline_config import PipelineConfig
from backend.domain.razbor import Razbor
from backend.domain.shortlist import ShortlistBatch, ShortlistItem
from backend.domain.vote import BallotTopic, PersonalVote
from backend.domain.voting_cycle import VotingCycle

_logger = logging.getLogger(__name__)


def _cosine(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if not na or not nb:
        return 0.0
    return dot / (na * nb)


def _searchable_material(material: Material | None, role_filter: str | None) -> Material | None:
    if material is None or material.status != MaterialStatus.READY:
        return None
    if role_filter and role_filter not in material.roles:
        return None
    return material


def _snippet(content: str) -> str:
    text = content.strip()
    if len(text) <= 180:
        return text
    return text[:177] + "..."


def _chunk_score(chunk: KnowledgeChunk, query_embedding: list[float], tokens: set[str]) -> float:
    vector_score = _cosine(query_embedding, chunk.embedding)
    if not tokens:
        return 0.7 * vector_score
    text = chunk.content_md.lower()
    fts_score = sum(1.0 for token in tokens if token in text) / len(tokens)
    return 0.7 * vector_score + 0.3 * fts_score


def _hit_for_chunk(
    materials: Any,
    chunk: KnowledgeChunk,
    query_embedding: list[float],
    tokens: set[str],
    role_filter: str | None,
) -> KnowledgeHit | None:
    material = materials.get(chunk.material_id) if materials is not None else None
    ready = _searchable_material(material, role_filter)
    if ready is None:
        return None
    score = _chunk_score(chunk, query_embedding, tokens)
    if score <= 0:
        return None
    return KnowledgeHit(
        material_id=ready.id,
        material_slug=ready.slug,
        chunk_index=chunk.chunk_index,
        snippet=_snippet(chunk.content_md),
        score=score,
    )


def _page_best_hits(scored: list[KnowledgeHit], *, limit: int, offset: int) -> list[KnowledgeHit]:
    # Dedupe by material_id — best score wins (D-61 / Pitfall 2).
    best: dict[int, KnowledgeHit] = {}
    for hit in scored:
        existing = best.get(hit.material_id)
        if existing is None or hit.score > existing.score:
            best[hit.material_id] = hit
    ranked = sorted(best.values(), key=lambda hit: hit.score, reverse=True)
    start = max(offset, 0)
    if limit < 1:
        return []
    return ranked[start : start + limit]


def _reject_stale_vote(
    existing: PersonalVote | None,
    cycle_id: str,
    user_id: str,
    topic_id: str,
    expected_updated_at: datetime | None,
) -> None:
    if existing is None:
        if expected_updated_at is not None:
            raise VoteConflictError(cycle_id, user_id)
        return
    if existing.topic_id == topic_id:
        return
    # A→B change requires matching expected_updated_at (strict CAS in 03-04)
    if expected_updated_at is None or existing.updated_at != expected_updated_at:
        raise VoteConflictError(cycle_id, user_id)


def _next_topic_votes(topic: BallotTopic, previous_topic: str | None, topic_id: str) -> int:
    votes = topic.votes
    if previous_topic == topic.id and previous_topic != topic_id:
        votes = max(0, votes - 1)
    if topic.id == topic_id and previous_topic != topic_id:
        votes = votes + 1
    return votes


def _retally_topics(
    topics: list[BallotTopic],
    *,
    previous_topic: str | None,
    topic_id: str,
) -> list[BallotTopic]:
    updated: list[BallotTopic] = []
    for topic in topics:
        votes = _next_topic_votes(topic, previous_topic, topic_id)
        updated.append(replace(topic, votes=votes) if votes != topic.votes else topic)
    return updated


@dataclass(frozen=True)
class InMemoryPingEntry:
    id: str
    user_id: str | None
    kind: str
    payload: dict = field(default_factory=dict)


class InMemoryPingRecorder:
    def __init__(self) -> None:
        self._entries: list[InMemoryPingEntry] = []
        self._next_id = 1

    def record(
        self,
        *,
        user_id: str | None,
        kind: str,
        payload: dict,
    ) -> str:
        entry_id = str(self._next_id)
        self._next_id += 1
        self._entries.append(
            InMemoryPingEntry(
                id=entry_id,
                user_id=user_id,
                kind=kind,
                payload=dict(payload),
            )
        )
        return entry_id

    def entries_for(self, user_id: str | None) -> list[InMemoryPingEntry]:
        return [e for e in self._entries if e.user_id == user_id]

    @property
    def entries(self) -> list[InMemoryPingEntry]:
        return list(self._entries)


class InMemoryShortlistRepository:
    """In-memory ShortlistRepository — empty by default (D-80)."""

    def __init__(
        self,
        batch: ShortlistBatch | None = None,
        materials: InMemoryMaterialRepository | None = None,
    ) -> None:
        self._batch = batch
        self._materials = materials

    def attach_materials(self, materials: InMemoryMaterialRepository | None) -> None:
        """Overlay material_status from materials repo (live-join fidelity; ADUX-05)."""
        self._materials = materials

    def _overlay_batch(self, batch: ShortlistBatch | None) -> ShortlistBatch | None:
        if batch is None or self._materials is None:
            return batch
        overlaid: list[ShortlistItem] = []
        for item in batch.items:
            material = self._materials.get(item.material_id)
            if material is None:
                overlaid.append(item)
            else:
                overlaid.append(replace(item, material_status=material.status.value))
        return replace(batch, items=tuple(overlaid))

    def get_current_batch(self) -> ShortlistBatch | None:
        # WR-03: match the live `sent_at IS NULL` contract — a claimed batch is no longer
        # "current" (mirrors SupabaseShortlistRepository.get_current_batch).
        if self._batch is None or self._batch.sent_at is not None:
            return None
        return self._overlay_batch(self._batch)

    def get_latest_batch(self) -> ShortlistBatch | None:
        """Most recent batch regardless of sent_at (D-89 already-sent signal)."""
        return self._overlay_batch(self._batch)

    def seed(self, batch: ShortlistBatch | None) -> None:
        self._batch = batch

    def set_decision(
        self,
        *,
        batch_id: int,
        material_id: int,
        decision: str,
        actor_user_id: str,
        decided_at: datetime,
    ) -> ShortlistBatch:
        if self._batch is None or self._batch.id != batch_id:
            raise ShortlistNotFoundError(batch_id=batch_id, material_id=material_id)
        updated: list[ShortlistItem] = []
        found = False
        for item in self._batch.items:
            if item.material_id == material_id:
                found = True
                updated.append(
                    ShortlistItem(
                        material_id=item.material_id,
                        rank=item.rank,
                        title=item.title,
                        material_status=item.material_status,
                        decision=decision,
                        score=item.score,
                        score_factors=item.score_factors,
                        decided_by=actor_user_id,
                        decided_at=decided_at,
                        dek=item.dek,
                        body_markdown=item.body_markdown,
                        provenance_label=item.provenance_label,
                        slug=item.slug,
                        reading_minutes=item.reading_minutes,
                    )
                )
            else:
                updated.append(item)
        if not found:
            raise ShortlistNotFoundError(batch_id=batch_id, material_id=material_id)
        self._batch = ShortlistBatch(
            id=self._batch.id,
            week_start=self._batch.week_start,
            sent_at=self._batch.sent_at,
            items=tuple(updated),
        )
        return self._batch

    def claim_sent(
        self,
        *,
        batch_id: int,
        sent_at: datetime,
    ) -> ShortlistBatch:
        if self._batch is None or self._batch.id != batch_id:
            raise ShortlistNotFoundError(batch_id=batch_id)
        if self._batch.sent_at is not None:
            raise AlreadySentError(batch_id)
        # Persist overlaid statuses so claim+publish pool matches live materials join (ADUX-05).
        overlaid = self._overlay_batch(self._batch)
        assert overlaid is not None  # nosec B101 - test double invariant, never shipped.
        self._batch = ShortlistBatch(
            id=overlaid.id,
            week_start=overlaid.week_start,
            sent_at=sent_at,
            items=overlaid.items,
        )
        return self._batch

    def release_claim(self, *, batch_id: int) -> None:
        """Reset sent_at to None (CR-01 compensation) so a failed publish can retry."""
        if self._batch is None or self._batch.id != batch_id:
            return
        self._batch = ShortlistBatch(
            id=self._batch.id,
            week_start=self._batch.week_start,
            sent_at=None,
            items=self._batch.items,
        )


class InMemoryProfileRepository:
    def __init__(self) -> None:
        self._by_id: dict[str, CurrentUser] = {}

    def get_or_upsert(self, user_id: str, email: str) -> CurrentUser:
        existing = self._by_id.get(user_id)
        if existing is not None and existing.email == email:
            return existing
        display_name = existing.display_name if existing is not None else None
        user = CurrentUser(
            id=user_id,
            email=email,
            role="employee",
            display_name=display_name,
        )
        self._by_id[user_id] = user
        return user

    def set_display_name(self, user_id: str, display_name: str) -> CurrentUser:
        existing = self._by_id.get(user_id)
        if existing is None:
            raise KeyError(f"profile not found: {user_id}")
        user = CurrentUser(
            id=existing.id,
            email=existing.email,
            role=existing.role,
            display_name=display_name,
        )
        self._by_id[user_id] = user
        return user

    def list_digest_recipients(self) -> list[Recipient]:
        """D-01/D-02: every profile with a usable email; malformed rows are logged, not counted."""
        recipients: list[Recipient] = []
        for user in self._by_id.values():
            if is_usable_email(user.email):
                recipients.append(
                    Recipient(email=user.email, display_name=user.display_name)
                )
            else:
                _logger.info(
                    "digest audience: excluding profile id=%s email=%r (unusable)",
                    user.id,
                    user.email,
                )
        return recipients


class InMemoryMaterialRepository:
    def __init__(self, materials: list[Material] | None = None) -> None:
        self._by_id: dict[int, Material] = {m.id: m for m in (materials or [])}
        self._by_slug: dict[str, Material] = {m.slug: m for m in (materials or [])}

    def get(self, material_id: int) -> Material | None:
        return self._by_id.get(material_id)

    def get_by_slug(self, slug: str) -> Material | None:
        return self._by_slug.get(slug)

    def save(self, material: Material) -> Material:
        self._by_id[material.id] = material
        self._by_slug[material.slug] = material
        return material


class InMemoryKnowledgeChunkRepository:
    """In-memory chunks with hybrid search (cosine 0.7 + FTS 0.3) for unit tests."""

    def __init__(self, materials: Any | None = None) -> None:
        self._chunks: list[KnowledgeChunk] = []
        self._next_id = 1
        self._materials = materials

    def replace_for_material(self, material_id: int, chunks: list[KnowledgeChunk]) -> list[KnowledgeChunk]:
        self._chunks = [c for c in self._chunks if c.material_id != material_id]
        stored: list[KnowledgeChunk] = []
        for chunk in chunks:
            stored_chunk = KnowledgeChunk(
                id=self._next_id,
                material_id=chunk.material_id,
                chunk_index=chunk.chunk_index,
                heading=chunk.heading,
                content_md=chunk.content_md,
                embedding=list(chunk.embedding),
                embedding_model_id=chunk.embedding_model_id,
                content_sha256=chunk.content_sha256,
                created_at=chunk.created_at,
            )
            self._next_id += 1
            stored.append(stored_chunk)
            self._chunks.append(stored_chunk)
        return stored

    def list_all(self) -> list[KnowledgeChunk]:
        return list(self._chunks)

    def search(
        self,
        *,
        query_embedding: list[float],
        query_text: str,
        role_filter: str | None,
        limit: int,
        offset: int,
    ) -> list[KnowledgeHit]:
        tokens = {t.lower() for t in re.findall(r"\w+", query_text, flags=re.UNICODE) if t}
        scored = [
            hit
            for chunk in self._chunks
            if (hit := _hit_for_chunk(self._materials, chunk, query_embedding, tokens, role_filter))
            is not None
        ]
        return _page_best_hits(scored, limit=limit, offset=offset)


class InMemoryVotingCycleReader:
    """In-memory VotingCycleReader — returns seeded cycles as-is (selection in use-case)."""

    def __init__(self, cycles: list[VotingCycle] | None = None) -> None:
        self._cycles: list[VotingCycle] = list(cycles or [])

    def seed(self, cycles: list[VotingCycle]) -> None:
        self._cycles = list(cycles)

    def list_cycles(self) -> list[VotingCycle]:
        return list(self._cycles)


class InMemoryVoteRepository:
    """In-memory VoteRepository keyed by (cycle_id, user_id) — PK one-row guarantee."""

    def __init__(
        self,
        topics_by_cycle: dict[str, list[BallotTopic]] | None = None,
    ) -> None:
        self._topics: dict[str, list[BallotTopic]] = {
            cycle_id: list(topics) for cycle_id, topics in (topics_by_cycle or {}).items()
        }
        self._votes: dict[tuple[str, str], PersonalVote] = {}

    def seed_topics(self, cycle_id: str, topics: list[BallotTopic]) -> None:
        self._topics[cycle_id] = list(topics)

    def list_topics_with_counts(self, cycle_id: str) -> list[BallotTopic]:
        return list(self._topics.get(cycle_id, []))

    def get_vote(self, cycle_id: str, user_id: str) -> PersonalVote | None:
        return self._votes.get((cycle_id, user_id))

    def vote_count_for(self, cycle_id: str) -> int:
        return sum(1 for key in self._votes if key[0] == cycle_id)

    def upsert_vote(
        self,
        *,
        cycle_id: str,
        user_id: str,
        topic_id: str,
        expected_updated_at: datetime | None,
    ) -> PersonalVote:
        key = (cycle_id, user_id)
        existing = self._votes.get(key)

        _reject_stale_vote(existing, cycle_id, user_id, topic_id, expected_updated_at)

        previous_topic = existing.topic_id if existing is not None else None
        now = datetime.now(timezone.utc)
        personal = PersonalVote(topic_id=topic_id, updated_at=now)
        self._votes[key] = personal
        self._topics[cycle_id] = _retally_topics(
            self._topics.get(cycle_id, []),
            previous_topic=previous_topic,
            topic_id=topic_id,
        )
        return personal


class InMemoryIssueRepository:
    """In-memory IssueRepository — selects latest published_at (D-24)."""

    def __init__(self, issues: list[Issue] | None = None) -> None:
        self._issues: list[Issue] = list(issues or [])
        self._next_id = 1

    def seed(self, issues: list[Issue]) -> None:
        self._issues = list(issues)

    def get_latest_published(self) -> Issue | None:
        published = [i for i in self._issues if i.published_at is not None]
        if not published:
            return None
        return max(published, key=lambda i: i.published_at)

    def get_by_number(self, number: int) -> Issue | None:
        for issue in self._issues:
            if issue.number == number and issue.published_at is not None:
                return issue
        return None

    def list_past_published(self) -> list[Issue]:
        current = self.get_latest_published()
        published = [i for i in self._issues if i.published_at is not None]
        if current is None:
            return sorted(published, key=lambda i: i.published_at, reverse=True)
        return sorted(
            [i for i in published if i.id != current.id],
            key=lambda i: i.published_at,
            reverse=True,
        )

    def publish(
        self,
        *,
        period_label: str,
        title: str,
        editor: str | None,
        published_at: datetime,
        items: list[IssueItem] | tuple[IssueItem, ...],
    ) -> Issue:
        numbers = [i.number for i in self._issues]
        number = (max(numbers) + 1) if numbers else 1
        issue_id = f"issue-{self._next_id}"
        self._next_id += 1
        issue = Issue(
            id=issue_id,
            number=number,
            period_label=period_label,
            title=title,
            editor=editor,
            published_at=published_at,
            items=tuple(items),
        )
        self._issues.append(issue)
        return issue


class InMemoryDigestPublisher:
    """In-memory DigestPublisher — simulates migration 005's atomic claim+publish RPC.

    Claims the batch, publishes its approved∩ready issue, and returns a DigestPublication.
    On any publish failure it releases the claim (CR-01 compensation) so the fake mirrors the
    RPC's all-or-nothing behavior. Repos are resolved lazily via callables so composition can
    reassign ``container.shortlist`` after wiring (HTTP tests swap it post-build).
    """

    def __init__(
        self,
        shortlist_provider: Any,
        issues_provider: Any,
        *,
        delivery_status: str = "stubbed",
    ) -> None:
        self._shortlist_provider = shortlist_provider
        self._issues_provider = issues_provider
        self._delivery_status = delivery_status

    def claim_and_publish(
        self,
        *,
        batch_id: int,
        sent_at: datetime,
        period_label: str,
        title: str,
        material_ids: list[int] | None = None,
        recipient_count: int = 0,
    ) -> DigestPublication:
        shortlist = self._shortlist_provider()
        issues = self._issues_provider()
        claimed = shortlist.claim_sent(batch_id=batch_id, sent_at=sent_at)
        try:
            pool = sorted(
                [
                    item
                    for item in claimed.items
                    if item.decision == "approved" and item.material_status == "ready"
                ],
                key=lambda item: item.rank,
            )
            if not pool:
                raise EmptySendPoolError(batch_id=batch_id)
            if material_ids is not None:
                by_id = {item.material_id: item for item in pool}
                # CR-01/WR-05: material_ids is the publication order (may be the admin-visible
                # top-5 subset). Require every requested id to be approved∩ready; ignore extras.
                if any(mid not in by_id for mid in material_ids):
                    raise EmptySendPoolError(batch_id=batch_id)
                pool = [by_id[mid] for mid in material_ids]
                if not pool:
                    raise EmptySendPoolError(batch_id=batch_id)
            issue_items = tuple(
                IssueItem(
                    slug=f"material-{item.material_id}",
                    title=item.title,
                    position=index,
                    format="article",
                    reading_minutes=5,
                )
                for index, item in enumerate(pool, start=1)
            )
            published = issues.publish(
                period_label=period_label,
                title=title,
                editor=None,
                published_at=sent_at,
                items=issue_items,
            )
        except Exception:
            shortlist.release_claim(batch_id=batch_id)
            raise
        planned = recipient_count
        return DigestPublication(
            batch_id=claimed.id,
            issue_number=published.number,
            issue_url=f"/issues/{published.number}",
            delivery_status=self._delivery_status,
            recipient_count=planned,
        )


class InMemoryRazborRepository:
    """In-memory RazborRepository — meeting_at DESC NULLS LAST, created_at DESC (RAZB-01)."""

    def __init__(self, razbors: list[Razbor] | None = None) -> None:
        self._razbors: list[Razbor] = list(razbors or [])

    def seed(self, razbors: list[Razbor]) -> None:
        self._razbors = list(razbors)

    def list_for_reader(self) -> list[Razbor]:
        return sorted(
            self._razbors,
            key=lambda r: (
                r.meeting_at is None,
                -(r.meeting_at.timestamp()) if r.meeting_at is not None else 0.0,
                -r.created_at.timestamp(),
            ),
        )

    def get(self, razbor_id: int) -> Razbor | None:
        for razbor in self._razbors:
            if razbor.id == razbor_id:
                return razbor
        return None


class InMemoryPipelineConfigRepository:
    """In-memory PipelineConfigRepository — absent by default (D-11 empty state).

    Records every save so route tests can assert zero writes on a validation reject
    (D-03/D-07).
    """

    def __init__(self, config: PipelineConfig | None = None) -> None:
        self._config = config
        self.saves: list[PipelineConfig] = []

    @property
    def save_count(self) -> int:
        return len(self.saves)

    def get(self) -> PipelineConfig | None:
        return self._config

    def save(self, *, yaml: str, updated_at: datetime) -> PipelineConfig:
        stored = PipelineConfig(yaml=yaml, updated_at=updated_at)
        self._config = stored
        self.saves.append(stored)
        return stored


class InMemoryPipelineConfigValidator:
    """Accept-all tracer validator (16-01 happy path); records calls for 16-02 asserts."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def validate(self, yaml_text: str) -> None:
        self.calls.append(yaml_text)


class InMemoryIngestSourceRepository:
    """In-memory IngestSourceRepository with write log for zero-write asserts (SRC-03, D-21).

    Stable list order: created_at ascending then id ascending. Auto-increment ids.
    """

    def __init__(self, sources: list[IngestSource] | None = None) -> None:
        self._sources: list[IngestSource] = list(sources or [])
        self._next_id = (max((s.id for s in self._sources), default=0) + 1)
        self.adds: list[IngestSource] = []
        self.writes: list[str] = []

    @property
    def write_count(self) -> int:
        return len(self.writes)

    def list(self) -> list[IngestSource]:
        return sorted(self._sources, key=lambda s: (s.created_at, s.id))

    def add(
        self,
        *,
        kind: str,
        source_id: str,
        label: str | None,
        is_enabled: bool = True,
    ) -> IngestSource:
        now = datetime.now(timezone.utc)
        row = IngestSource(
            id=self._next_id,
            kind=kind,
            source_id=source_id,
            label=label,
            is_enabled=is_enabled,
            created_at=now,
            updated_at=now,
        )
        self._next_id += 1
        self._sources.append(row)
        self.adds.append(row)
        self.writes.append("add")
        return row

    def set_enabled(self, source_id_pk: int, *, is_enabled: bool) -> IngestSource:
        for index, row in enumerate(self._sources):
            if row.id == source_id_pk:
                updated = IngestSource(
                    id=row.id,
                    kind=row.kind,
                    source_id=row.source_id,
                    label=row.label,
                    is_enabled=is_enabled,
                    created_at=row.created_at,
                    updated_at=datetime.now(timezone.utc),
                )
                self._sources[index] = updated
                self.writes.append("set_enabled")
                return updated
        raise KeyError(f"ingest source {source_id_pk} not found")

    def delete(self, source_id_pk: int) -> None:
        for index, row in enumerate(self._sources):
            if row.id == source_id_pk:
                del self._sources[index]
                self.writes.append("delete")
                return
        raise KeyError(f"ingest source {source_id_pk} not found")


class InMemoryIngestionScheduleRepository:
    """In-memory IngestionScheduleRepository with update_calls for zero-write asserts (ING-06, D-14).

    ``get()`` returns domain defaults when ``current`` is None (no insert).
    ``update()`` upserts the singleton and increments ``update_calls``.
    """

    def __init__(self, current: IngestionSchedule | None = None) -> None:
        self.current: IngestionSchedule | None = current
        self.update_calls: int = 0

    def get(self) -> IngestionSchedule:
        if self.current is None:
            return default_ingestion_schedule()
        return self.current

    def update(
        self,
        *,
        enabled: bool,
        time_of_day: time,
        days_of_week: tuple[int, ...],
    ) -> IngestionSchedule:
        self.update_calls += 1
        prev = self.current
        self.current = IngestionSchedule(
            enabled=enabled,
            time_of_day=time_of_day,
            days_of_week=days_of_week,
            last_run_at=prev.last_run_at if prev is not None else None,
            updated_at=datetime.now(timezone.utc),
        )
        return self.current
