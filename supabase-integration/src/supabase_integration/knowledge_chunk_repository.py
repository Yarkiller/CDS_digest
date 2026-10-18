"""KnowledgeChunkRepository adapter — hybrid search via SQL RPC (service_role)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Protocol

from backend.domain.errors import PersistenceError
from backend.domain.knowledge import KnowledgeChunk, KnowledgeHit


class _SupabaseClient(Protocol):
    def table(self, name: str) -> Any: ...

    def rpc(self, fn: str, params: dict[str, Any] | None = None) -> Any: ...


def _parse_dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    text = str(value).replace("Z", "+00:00")
    return datetime.fromisoformat(text)


def _row_to_hit(row: dict[str, Any]) -> KnowledgeHit:
    return KnowledgeHit(
        material_id=int(row["material_id"]),
        material_slug=str(row["material_slug"]),
        chunk_index=int(row["chunk_index"]),
        snippet=str(row.get("snippet") or ""),
        score=float(row.get("score") or 0.0),
    )


def _row_to_chunk(row: dict[str, Any]) -> KnowledgeChunk:
    emb = row.get("embedding")
    if isinstance(emb, str):
        # PostgREST may return "[1,2,...]"
        emb = [float(x) for x in emb.strip("[]").split(",") if x.strip()]
    elif not isinstance(emb, list):
        emb = []
    return KnowledgeChunk(
        id=int(row["id"]),
        material_id=int(row["material_id"]),
        chunk_index=int(row["chunk_index"]),
        heading=str(row["heading"]) if row.get("heading") is not None else None,
        content_md=str(row["content_md"]),
        embedding=[float(x) for x in emb],
        embedding_model_id=str(row["embedding_model_id"]),
        content_sha256=str(row["content_sha256"]),
        created_at=_parse_dt(row.get("created_at") or datetime.now(timezone.utc).isoformat()),
    )


class SupabaseKnowledgeChunkRepository:
    """Live knowledge chunks — search via SECURITY INVOKER RPC (not list_all+Python)."""

    def __init__(self, client: _SupabaseClient) -> None:
        self._client = client

    def search(
        self,
        *,
        query_embedding: list[float],
        query_text: str,
        role_filter: str | None,
        limit: int,
        offset: int,
    ) -> list[KnowledgeHit]:
        params: dict[str, Any] = {
            "query_embedding": query_embedding,
            "query_text": query_text,
            "role_filter": role_filter,
            "result_limit": limit,
            "result_offset": offset,
        }
        try:
            result = self._client.rpc("search_knowledge_chunks", params).execute()
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001 — map SDK failures at boundary
            raise PersistenceError(f"knowledge_chunks search failed: {exc}") from exc

        rows = getattr(result, "data", None) or []
        return [_row_to_hit(row) for row in rows if isinstance(row, dict)]

    def list_all(self) -> list[KnowledgeChunk]:
        try:
            result = (
                self._client.table("knowledge_chunks")
                .select(
                    "id,material_id,chunk_index,heading,content_md,"
                    "embedding,embedding_model_id,content_sha256,created_at"
                )
                .execute()
            )
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise PersistenceError(f"knowledge_chunks list_all failed: {exc}") from exc

        rows = getattr(result, "data", None) or []
        return [_row_to_chunk(row) for row in rows if isinstance(row, dict)]

    def replace_for_material(self, material_id: int, chunks: list[KnowledgeChunk]) -> list[KnowledgeChunk]:
        try:
            (
                self._client.table("knowledge_chunks")
                .delete()
                .eq("material_id", material_id)
                .execute()
            )
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise PersistenceError(
                f"knowledge_chunks replace delete failed: {exc}"
            ) from exc

        if not chunks:
            return []

        payload = [
            {
                "material_id": material_id,
                "chunk_index": c.chunk_index,
                "heading": c.heading,
                "content_md": c.content_md,
                "embedding": c.embedding,
                "embedding_model_id": c.embedding_model_id,
                "content_sha256": c.content_sha256,
            }
            for c in chunks
        ]
        try:
            result = (
                self._client.table("knowledge_chunks")
                .upsert(payload, on_conflict="material_id,chunk_index")
                .execute()
            )
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise PersistenceError(
                f"knowledge_chunks replace upsert failed: {exc}"
            ) from exc

        rows = getattr(result, "data", None) or []
        if rows:
            return [_row_to_chunk(row) for row in rows if isinstance(row, dict)]
        return list(chunks)
