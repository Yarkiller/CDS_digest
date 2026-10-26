"""mark_material_ready — status-only triage promote (ADUX-05; D-06 / D-08 / D-09 / D-10)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from backend.application.ports.material_repository import MaterialRepository
from backend.domain.errors import MaterialNotFoundError, PersistenceError
from backend.domain.material import Material


@dataclass(frozen=True, slots=True)
class MarkReadyItemResult:
    """Per-id batch outcome for mark_materials_ready (D-08; ADUX-05)."""

    material_id: int
    ok: bool
    status: str | None = None
    error: str | None = None


def mark_material_ready(
    repo: MaterialRepository,
    material_id: int,
    *,
    now: datetime | None = None,
) -> Material:
    material = repo.get(material_id)
    if material is None:
        raise MaterialNotFoundError(material_id)
    clock = now or datetime.now(timezone.utc)
    updated = material.with_ready_status(now=clock)
    if updated is material:
        return material
    return repo.save(updated)


def mark_materials_ready(
    repo: MaterialRepository,
    material_ids: list[int],
    *,
    now: datetime | None = None,
) -> list[MarkReadyItemResult]:
    """Promote many materials independently; never abort the batch on one failure (D-08)."""
    results: list[MarkReadyItemResult] = []
    for material_id in material_ids:
        try:
            material = mark_material_ready(repo, material_id, now=now)
        except MaterialNotFoundError:
            results.append(
                MarkReadyItemResult(
                    material_id=material_id,
                    ok=False,
                    status=None,
                    error="material_not_found",
                )
            )
            continue
        except PersistenceError:
            results.append(
                MarkReadyItemResult(
                    material_id=material_id,
                    ok=False,
                    status=None,
                    error="materials_unavailable",
                )
            )
            continue
        except Exception:
            results.append(
                MarkReadyItemResult(
                    material_id=material_id,
                    ok=False,
                    status=None,
                    error="unexpected_error",
                )
            )
            continue
        results.append(
            MarkReadyItemResult(
                material_id=material_id,
                ok=True,
                status=material.status.value,
                error=None,
            )
        )
    return results
