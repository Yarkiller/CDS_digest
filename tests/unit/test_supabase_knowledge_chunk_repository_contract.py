"""Contract tests for SupabaseKnowledgeChunkRepository (offline stubs — no network)."""

from __future__ import annotations

from typing import Any

import pytest

from backend.domain.errors import PersistenceError
from backend.domain.knowledge import KnowledgeHit


class _FakeExecuteResult:
    def __init__(self, data: list[dict[str, Any]] | None = None) -> None:
        self.data = data if data is not None else []


class FakeSupabaseClient:
    """Minimal stub supporting table(...) and rpc(...)."""

    def __init__(self) -> None:
        self.rpc_calls: list[tuple[str, dict[str, Any]]] = []
        self.rpc_result: list[dict[str, Any]] = []
        self.fail_rpc = False
        self.tables: dict[str, list[dict[str, Any]]] = {"knowledge_chunks": []}

    def rpc(self, fn: str, params: dict[str, Any] | None = None) -> Any:
        self.rpc_calls.append((fn, dict(params or {})))

        class _Chain:
            def __init__(self, outer: FakeSupabaseClient) -> None:
                self._outer = outer

            def execute(self) -> _FakeExecuteResult:
                if self._outer.fail_rpc:
                    raise RuntimeError("simulated rpc failure")
                return _FakeExecuteResult(list(self._outer.rpc_result))

        return _Chain(self)

    def table(self, name: str) -> Any:
        rows = self.tables.setdefault(name, [])

        class _Q:
            def __init__(self) -> None:
                self._op: str | None = None
                self._payload: Any = None

            def select(self, *_a: Any, **_k: Any) -> "_Q":
                self._op = "select"
                return self

            def delete(self) -> "_Q":
                self._op = "delete"
                return self

            def eq(self, *_a: Any, **_k: Any) -> "_Q":
                return self

            def upsert(self, payload: Any, **_k: Any) -> "_Q":
                self._op = "upsert"
                self._payload = payload
                return self

            def execute(self) -> _FakeExecuteResult:
                if self._op == "upsert":
                    if isinstance(self._payload, list):
                        rows.extend(self._payload)
                    elif isinstance(self._payload, dict):
                        rows.append(self._payload)
                    return _FakeExecuteResult(
                        self._payload if isinstance(self._payload, list) else [self._payload]
                    )
                if self._op == "delete":
                    rows.clear()
                    return _FakeExecuteResult([])
                return _FakeExecuteResult(list(rows))

        return _Q()


def test_search_calls_hybrid_rpc_with_params() -> None:
    from supabase_integration.knowledge_chunk_repository import SupabaseKnowledgeChunkRepository

    client = FakeSupabaseClient()
    client.rpc_result = [
        {
            "material_id": 7,
            "material_slug": "pgvector",
            "chunk_index": 0,
            "snippet": "Use HNSW indexes",
            "score": 0.91,
        }
    ]
    repo = SupabaseKnowledgeChunkRepository(client)
    embedding = [0.1] * 1024

    hits = repo.search(
        query_embedding=embedding,
        query_text="HNSW indexes",
        role_filter="ds",
        limit=5,
        offset=0,
    )

    assert len(client.rpc_calls) == 1
    fn, params = client.rpc_calls[0]
    assert fn == "search_knowledge_chunks"
    assert params["query_text"] == "HNSW indexes"
    assert params["role_filter"] == "ds"
    assert params["result_limit"] == 5
    assert params["result_offset"] == 0
    assert params["query_embedding"] == embedding
    assert len(hits) == 1
    assert isinstance(hits[0], KnowledgeHit)
    assert hits[0].material_slug == "pgvector"
    assert hits[0].score == pytest.approx(0.91)


def test_search_maps_sdk_errors_to_persistence_error() -> None:
    from supabase_integration.knowledge_chunk_repository import SupabaseKnowledgeChunkRepository

    client = FakeSupabaseClient()
    client.fail_rpc = True
    repo = SupabaseKnowledgeChunkRepository(client)

    with pytest.raises(PersistenceError, match="search"):
        repo.search(
            query_embedding=[0.0] * 1024,
            query_text="x",
            role_filter=None,
            limit=10,
            offset=0,
        )


def test_search_does_not_use_list_all_python_path() -> None:
    """Live adapter must invoke SQL/RPC — not pull all chunks for Python cosine."""
    import inspect

    from supabase_integration.knowledge_chunk_repository import SupabaseKnowledgeChunkRepository

    source = inspect.getsource(SupabaseKnowledgeChunkRepository.search)
    assert "rpc" in source
    assert "list_all" not in source
