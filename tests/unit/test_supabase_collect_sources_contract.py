"""Contract tests for SupabaseCollectSourceReader (offline fake client — no network)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest


class _FakeExecuteResult:
    def __init__(self, data: list[dict[str, Any]]) -> None:
        self.data = data


class _FakeQuery:
    def __init__(self, table: "_FakeTable") -> None:
        self._table = table
        self._op: str | None = None
        self._payload: Any = None
        self._filters: list[tuple[str, Any]] = []
        self._order: list[tuple[str, bool]] = []

    def select(self, cols: str = "*") -> "_FakeQuery":
        if self._op is None:
            self._op = "select"
        self._table.selected = cols
        return self

    def update(self, payload: dict[str, Any]) -> "_FakeQuery":
        self._op = "update"
        self._payload = dict(payload)
        self._table.last_update = dict(payload)
        return self

    def eq(self, column: str, value: Any) -> "_FakeQuery":
        self._filters.append((column, value))
        self._table.last_filters.append((column, value))
        return self

    def order(self, column: str, *, desc: bool = False) -> "_FakeQuery":
        self._order.append((column, desc))
        return self

    def execute(self) -> _FakeExecuteResult:
        if self._table.raise_error is not None:
            error = self._table.raise_error
            self._table.raise_error = None
            raise error
        if self._table.fail_next:
            self._table.fail_next = False
            raise RuntimeError("simulated supabase failure")

        if self._op == "update":
            assert isinstance(self._payload, dict)
            matched: list[dict[str, Any]] = []
            for index, row in enumerate(self._table.rows):
                if all(row.get(col) == val for col, val in self._filters):
                    updated = {**row, **self._payload}
                    self._table.rows[index] = updated
                    matched.append(dict(updated))
            return _FakeExecuteResult(matched)

        rows = list(self._table.rows)
        for column, value in self._filters:
            rows = [r for r in rows if r.get(column) == value]
        for column, desc in reversed(self._order):
            rows = sorted(rows, key=lambda r: r.get(column), reverse=desc)
        return _FakeExecuteResult(rows)


class _FakeTable:
    def __init__(self, name: str) -> None:
        self.name = name
        self.rows: list[dict[str, Any]] = []
        self.fail_next = False
        self.raise_error: BaseException | None = None
        self.last_update: dict[str, Any] | None = None
        self.last_filters: list[tuple[str, Any]] = []
        self.selected: str | None = None

    def query(self) -> _FakeQuery:
        return _FakeQuery(self)


class FakeSupabaseClient:
    def __init__(self) -> None:
        self.tables: dict[str, _FakeTable] = {
            "pipeline_ingest_sources": _FakeTable("pipeline_ingest_sources"),
        }

    def table(self, name: str) -> _FakeQuery:
        if name not in self.tables:
            raise AssertionError(f"unexpected table: {name}")
        return self.tables[name].query()


def test_list_enabled_sources_filters_is_enabled_and_parses_cursor() -> None:
    from ingestion_service.adapters.supabase_collect_sources import (
        SupabaseCollectSourceReader,
    )
    from ingestion_service.application.ports.collect_sources import EnabledSource

    client = FakeSupabaseClient()
    client.tables["pipeline_ingest_sources"].rows = [
        {
            "id": 1,
            "kind": "channel",
            "source_id": "UC_disabled",
            "is_enabled": False,
            "last_seen_published_at": None,
            "last_seen_video_id": None,
            "created_at": "2026-10-17T10:00:00Z",
        },
        {
            "id": 2,
            "kind": "channel",
            "source_id": "UC_x5XG1OV2P6uZZ5FSMdItQ",
            "is_enabled": True,
            "last_seen_published_at": "2026-10-17T09:00:00Z",
            "last_seen_video_id": "dQw4w9WgXcQ",
            "created_at": "2026-10-17T11:00:00Z",
        },
    ]
    reader = SupabaseCollectSourceReader(client)
    sources = reader.list_enabled_sources()
    assert len(sources) == 1
    src = sources[0]
    assert isinstance(src, EnabledSource)
    assert src.id == 2
    assert src.kind == "channel"
    assert src.source_id == "UC_x5XG1OV2P6uZZ5FSMdItQ"
    assert src.last_seen_published_at == datetime(
        2026, 10, 17, 9, 0, tzinfo=timezone.utc
    )
    assert src.last_seen_video_id == "dQw4w9WgXcQ"
    table = client.tables["pipeline_ingest_sources"]
    assert "is_enabled" in (table.selected or "")
    assert ("is_enabled", True) in table.last_filters


def test_advance_cursor_sends_update_payload_for_source_pk() -> None:
    from ingestion_service.adapters.supabase_collect_sources import (
        SupabaseCollectSourceReader,
    )

    client = FakeSupabaseClient()
    client.tables["pipeline_ingest_sources"].rows = [
        {
            "id": 7,
            "kind": "channel",
            "source_id": "UC_x5XG1OV2P6uZZ5FSMdItQ",
            "is_enabled": True,
            "last_seen_published_at": None,
            "last_seen_video_id": None,
            "created_at": "2026-10-17T11:00:00Z",
        },
    ]
    reader = SupabaseCollectSourceReader(client)
    published = datetime(2026, 10, 17, 9, 0, tzinfo=timezone.utc)
    reader.advance_cursor(7, published=published, video_id="dQw4w9WgXcQ")
    table = client.tables["pipeline_ingest_sources"]
    assert table.last_update is not None
    assert table.last_update["last_seen_video_id"] == "dQw4w9WgXcQ"
    assert "last_seen_published_at" in table.last_update
    assert ("id", 7) in table.last_filters


def test_sdk_exception_maps_to_collect_source_error() -> None:
    from ingestion_service.adapters.supabase_collect_sources import (
        SupabaseCollectSourceReader,
    )
    from ingestion_service.application.ports.collect_sources import CollectSourceError

    client = FakeSupabaseClient()
    client.tables["pipeline_ingest_sources"].fail_next = True
    reader = SupabaseCollectSourceReader(client)
    with pytest.raises(CollectSourceError):
        reader.list_enabled_sources()
