"""record_platform_ping use-case — PingRecorder port contract (PLAT-04 / D-10)."""

from __future__ import annotations

import ast
from pathlib import Path

from backend.application.use_cases.record_platform_ping import (
    PLATFORM_PING_KIND,
    record_platform_ping,
)
from backend.tests_support.in_memory import InMemoryPingRecorder


def test_record_platform_ping_stores_platform_ping_kind() -> None:
    pings = InMemoryPingRecorder()
    recorded_id = record_platform_ping(pings, user_id="user-uuid-1")

    assert recorded_id is not None
    entries = pings.entries_for("user-uuid-1")
    assert len(entries) == 1
    assert entries[0].kind == PLATFORM_PING_KIND
    assert entries[0].kind == "platform_ping"
    assert entries[0].user_id == "user-uuid-1"
    assert entries[0].id == recorded_id
    assert isinstance(entries[0].payload, dict)


def test_record_platform_ping_use_case_has_no_sdk_imports() -> None:
    path = (
        Path(__file__).resolve().parents[2]
        / "backend"
        / "src"
        / "backend"
        / "application"
        / "use_cases"
        / "record_platform_ping.py"
    )
    tree = ast.parse(path.read_text(encoding="utf-8"))
    forbidden = {"fastapi", "httpx", "supabase", "supabase_integration"}
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported.isdisjoint(forbidden)
