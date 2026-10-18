"""Composition root: wire adapters into use-cases."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from backend.application.ports.digest_publisher import DigestPublisher
from backend.application.ports.issue_repository import IssueRepository
from backend.application.ports.knowledge_chunk_repository import KnowledgeChunkRepository
from backend.application.ports.mailer import Mailer
from backend.application.ports.material_repository import MaterialRepository
from backend.application.ports.notebook_storage import NotebookStorage
from backend.application.ports.ping_recorder import PingRecorder
from backend.application.ports.profile_repository import ProfileRepository
from backend.application.ports.ingest_sources import IngestSourceRepository
from backend.application.ports.ingestion_schedule import IngestionScheduleRepository
from backend.application.ports.pipeline_config import (
    PipelineConfigRepository,
    PipelineConfigValidator,
)
from backend.application.ports.query_embedder import QueryEmbedder, StubQueryEmbedder
from backend.application.ports.razbor_repository import RazborRepository
from backend.application.ports.shortlist_repository import ShortlistRepository
from backend.application.ports.vote_repository import VoteRepository
from backend.application.ports.voting_cycle_reader import VotingCycleReader
from backend.application.use_cases.index_material_chunks import index_material_chunks
from backend.application.use_cases.publish_material import publish_material
from backend.application.use_cases.search_knowledge import DEFAULT_SEARCH_LIMIT, search_knowledge
from backend.domain.issue import Issue
from backend.domain.knowledge import KnowledgeHit
from backend.domain.material import Material
from backend.domain.voting_cycle import VotingCycle
from backend.infrastructure.local_notebook_storage import LocalNotebookStorage
from backend.infrastructure.stub_mailer import StubMailer
from backend.infrastructure.yaml_pipeline_config_validator import YamlPipelineConfigValidator
from backend.tests_support.in_memory import (
    InMemoryDigestPublisher,
    InMemoryIngestSourceRepository,
    InMemoryIngestionScheduleRepository,
    InMemoryIssueRepository,
    InMemoryKnowledgeChunkRepository,
    InMemoryMaterialRepository,
    InMemoryPingRecorder,
    InMemoryPipelineConfigRepository,
    InMemoryProfileRepository,
    InMemoryRazborRepository,
    InMemoryShortlistRepository,
    InMemoryVoteRepository,
    InMemoryVotingCycleReader,
)


@dataclass
class AppContainer:
    materials: MaterialRepository
    chunks: KnowledgeChunkRepository
    profiles: ProfileRepository
    pings: PingRecorder
    issues: IssueRepository
    voting_cycles: VotingCycleReader
    votes: VoteRepository
    embedder: QueryEmbedder
    razbors: RazborRepository
    notebook_storage: NotebookStorage
    shortlist: ShortlistRepository
    mailer: Mailer
    publisher: DigestPublisher
    # Declared here (deferred from 16-01) with None defaults so a bare AppContainer(...)
    # still constructs; build_in_memory_container wires the real adapter.
    pipeline_config: PipelineConfigRepository | None = None
    pipeline_config_validator: PipelineConfigValidator | None = None
    # D-21: ingest sources port — None until wired (503 ingest_sources_not_configured).
    ingest_sources: IngestSourceRepository | None = None
    # D-14: ingestion_schedule port — None until wired (503).
    ingestion_schedule: IngestionScheduleRepository | None = None

    def publish(self, material_id: int) -> Material:
        return publish_material(self.materials, material_id)

    def index(self, material_id: int, *, embedding_model_id: str, embed) -> list:
        return index_material_chunks(
            materials=self.materials,
            chunks=self.chunks,
            material_id=material_id,
            embedding_model_id=embedding_model_id,
            embed=embed,
        )

    def search(
        self,
        *,
        query_embedding: list[float] | None = None,
        query_text: str,
        role_filter: str | None = None,
        limit: int = DEFAULT_SEARCH_LIMIT,
        offset: int = 0,
    ) -> list[KnowledgeHit]:
        embedding = query_embedding if query_embedding is not None else self.embedder.embed(query_text)
        return search_knowledge(
            chunks=self.chunks,
            query_embedding=embedding,
            query_text=query_text,
            role_filter=role_filter,
            limit=limit,
            offset=offset,
        )


def build_in_memory_container(
    materials: list[Material] | None = None,
    issues: list[Issue] | None = None,
    voting_cycles: list[VotingCycle] | None = None,
    *,
    notebook_root: str | Path | None = None,
) -> AppContainer:
    """Default local wiring until supabase-integration adapters are connected."""
    materials_repo = InMemoryMaterialRepository(materials)
    shortlist_repo = InMemoryShortlistRepository(materials=materials_repo)
    root = Path(notebook_root) if notebook_root else Path(".")
    container = AppContainer(
        materials=materials_repo,
        chunks=InMemoryKnowledgeChunkRepository(materials=materials_repo),
        profiles=InMemoryProfileRepository(),
        pings=InMemoryPingRecorder(),
        issues=InMemoryIssueRepository(issues),
        voting_cycles=InMemoryVotingCycleReader(voting_cycles),
        votes=InMemoryVoteRepository(),
        embedder=StubQueryEmbedder(),
        razbors=InMemoryRazborRepository(),
        notebook_storage=LocalNotebookStorage(root),
        shortlist=shortlist_repo,
        mailer=StubMailer(),
        # Placeholder replaced below with a publisher bound to this container so tests that
        # reassign container.shortlist post-build are still resolved (lazy providers).
        publisher=None,  # type: ignore[arg-type]
    )
    container.publisher = InMemoryDigestPublisher(
        lambda: container.shortlist,
        lambda: container.issues,
    )
    container.pipeline_config = InMemoryPipelineConfigRepository()
    container.pipeline_config_validator = YamlPipelineConfigValidator()
    container.ingest_sources = InMemoryIngestSourceRepository()
    container.ingestion_schedule = InMemoryIngestionScheduleRepository()
    return container
