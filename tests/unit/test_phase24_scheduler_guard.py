"""ING-07 guard: ingest-collect import graph never reaches publish/send (D-09).

Two levels: AST scan of ingestion_service sources + runtime sys.modules after
importing ingestion_service.collect_cli. Production code is not modified here.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_SRC_ROOT = _REPO / "ingestion-service" / "src"
_PKG_ROOT = _SRC_ROOT / "ingestion_service"

FORBIDDEN_ROOTS = frozenset({"backend", "publish", "send"})


def _scan_forbidden_roots(
    src_root: Path, forbidden: frozenset[str]
) -> dict[str, set[str]]:
    """RED stub — returns empty until GREEN implements the AST walker."""
    del src_root, forbidden
    return {}


def test_import_graph_has_no_publish_roots() -> None:
    """AST: no Import/ImportFrom root intersects FORBIDDEN_ROOTS."""
    found = _scan_forbidden_roots(_PKG_ROOT, FORBIDDEN_ROOTS)
    scanned = list(_PKG_ROOT.rglob("*.py"))
    assert len(scanned) >= 10, f"anti-vacuum: expected >=10 .py files, got {len(scanned)}"
    assert found == {}, f"forbidden roots in import graph: {found}"


def test_runtime_modules_are_clean() -> None:
    """Runtime: import collect_cli in a subprocess; sys.modules roots stay clean."""
    code = (
        "import ingestion_service.collect_cli, sys; "
        "print('\\n'.join(sorted({m.split('.')[0] for m in sys.modules})))"
    )
    env = {**os.environ, "PYTHONPATH": str(_SRC_ROOT)}
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    roots = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    assert "ingestion_service" in roots, "anti-vacuum: collect_cli did not load"
    hits = roots & FORBIDDEN_ROOTS
    assert hits == set(), f"forbidden roots loaded at runtime: {hits}"


def test_collect_cli_does_not_load_ingest_entry_point() -> None:
    """Importing collect_cli must not pull in ingestion_service.cli."""
    code = (
        "import ingestion_service.collect_cli, sys; "
        "print('cli' if 'ingestion_service.cli' in sys.modules else 'ok')"
    )
    env = {**os.environ, "PYTHONPATH": str(_SRC_ROOT)}
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ok"


def test_collect_cli_exports_only_entry() -> None:
    """collect_cli exposes app + build_collect_deps; no run_ingest_pipeline attribute."""
    code = (
        "import ingestion_service.collect_cli as m; "
        "print(hasattr(m, 'app'), hasattr(m, 'build_collect_deps'), "
        "hasattr(m, 'run_ingest_pipeline'))"
    )
    env = {**os.environ, "PYTHONPATH": str(_SRC_ROOT)}
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "True True False"


def test_guard_catches_injected_violation() -> None:
    """Scanner is not a vacuum: injecting an existing root (json) must be found."""
    injected = frozenset({"json"})
    found = _scan_forbidden_roots(_PKG_ROOT, injected)
    assert found, "scanner must detect injected forbidden root 'json'"
    flat = set().union(*found.values()) if found else set()
    assert "json" in flat
