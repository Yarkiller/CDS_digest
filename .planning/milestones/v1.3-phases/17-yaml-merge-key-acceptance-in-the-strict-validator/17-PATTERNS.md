# Phase 17: YAML merge-key acceptance in the strict validator - Pattern Map

**Mapped:** 2026-10-14
**Files analyzed:** 3 (1 production modified, 1 test created, 1 test modified)
**Analogs found:** 3 / 3

> Scope is deliberately tiny (a single-adapter parse-path fix). Every expected file from the
> phase-specific guidance exists except `tests/unit/test_pipeline_config_merge.py`, which is
> **new** (confirmed absent — `git ls-files` returns nothing, and it is not in the
> `tests/unit/` listing). No file beyond the guidance set is named by `17-RESEARCH.md`.
>
> **Tracked-source gate:** all three files below were verified git-tracked with
> `git ls-files -- <path>` (non-empty output). No gitignored mirror path is emitted.
> The installed PyYAML source (`.venv/Lib/site-packages/yaml/constructor.py`) is an
> **external dependency reference**, not a repo analog — it is labelled as such and must
> never be edited.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `backend/src/backend/infrastructure/yaml_pipeline_config_validator.py` (MODIFIED) | adapter (validator) | transform (parse/validate) | **itself** — the existing `_StrictSafeLoader.construct_mapping` override (lines 36-56) | exact (self) |
| `tests/unit/test_pipeline_config_merge.py` (CREATED) | test (unit) | transform (parametrized corpus loops) | `tests/unit/test_pipeline_config_validator.py` | exact |
| `tests/unit/test_http_pipeline_config.py` (MODIFIED, +1 test) | test (integration / in-process HTTP) | request-response | same file: `_real_validator_admin_env()` (129-142) + `test_put_then_get_round_trip_returns_saved_yaml` (174-192) | exact (self) |

**Directory placement check:** the existing validator test lives in `tests/unit/`
(`testpaths = ["tests/unit"]`, `pythonpath = ["."]` in `pyproject.toml`), so the new test
module belongs there too — same directory, same import roots. **No `conftest.py` exists
anywhere in the repo** (verified by glob), so the new module must declare its own
module-level YAML-string constants rather than expect a shared fixture.

---

## Pattern Assignments

### `backend/src/backend/infrastructure/yaml_pipeline_config_validator.py` (adapter, transform)

**Analog:** itself. The new `flatten_mapping` override and the `construct_mapping` edit must
mirror the shape already present in the same file (`super()` delegation, `ConstructorError`
usage, module-level `_*_MESSAGE` constants). The plan's action text should point the executor
at these exact ranges and say "preserve this shape".

#### 1. The exact `construct_mapping` override to preserve (lines 36-56)

This is the shape the fix must keep. The bug is **line 43** running
`self.construct_object(...)` on the merge-tagged key node *before* line 56's `super()` can
reach `flatten_mapping`. The fix: `continue` on `key_node.tag == _MERGE_TAG`, and iterate the
pristine own-key snapshot instead of the possibly already-flattened `node.value`.

```36:56:backend/src/backend/infrastructure/yaml_pipeline_config_validator.py
class _StrictSafeLoader(yaml.SafeLoader):
    """SafeLoader that rejects duplicate mapping keys instead of silently last-wins."""

    def construct_mapping(self, node: MappingNode, deep: bool = False) -> dict[Any, Any]:
        if isinstance(node, MappingNode):
            seen: set[Any] = set()
            for key_node, _value_node in node.value:
                key = self.construct_object(key_node, deep=deep)
                try:
                    hash(key)
                except TypeError:
                    continue
                if key in seen:
                    raise ConstructorError(
                        "while constructing a mapping",
                        node.start_mark,
                        f"found duplicate key ({key!r})",
                        key_node.start_mark,
                    )
                seen.add(key)
        return super().construct_mapping(node, deep=deep)
```

**Invariants to preserve byte-for-byte (D-02/D-09):**
- the `ConstructorError` argument order and both marks (`node.start_mark`, `key_node.start_mark`);
- the exact message `f"found duplicate key ({key!r})"` — the HTTP tripwire compares rows against
  the validator's own output, but `test_duplicate_top_level_key_is_rejected_not_last_wins`
  asserts `errors[0].line == 2`, which is mark-derived and must not shift;
- `super().construct_mapping(node, deep=deep)` stays the last line (never call
  `flatten_mapping` explicitly here — the base class already does it via `super()`).

#### 2. Module-level message-constant block (lines 30-33) — the home for the two new messages

The new constants (`_MERGE_TAG`, `MAX_MERGE_DEPTH`, `MAX_MERGE_ENTRIES`,
`_MERGE_TOO_BIG_MESSAGE`, `_EXTRA_ANCHOR_KEY_MESSAGE`) sit beside these, per D-06. Note the
existing four are **siblings the reject envelope must remain uniform with**; the new merge-bound
message must be a *distinct* constant (D-06) — never a reuse of `_OVER_CAP_MESSAGE`.

```30:33:backend/src/backend/infrastructure/yaml_pipeline_config_validator.py
_OVER_CAP_MESSAGE = "Документ конфига превышает допустимый размер"
_NOT_A_TEXT_OBJECT_MESSAGE = "Ожидается объект с текстовыми ключами"
_TOO_DEEP_MESSAGE = "Документ YAML имеет слишком глубокую вложенность"
_UNREADABLE_MESSAGE = "Документ содержит недопустимые символы"
```

**Imports that must be extended** (lines 19-25): `SequenceNode` is **not imported yet** and is
required for the projection's sequence-source branch. `MappingNode` and `ConstructorError` are
already imported.

```19:25:backend/src/backend/infrastructure/yaml_pipeline_config_validator.py
import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from yaml.constructor import ConstructorError
from yaml.nodes import MappingNode

from backend.domain.errors import PipelineConfigValidationError
from backend.domain.pipeline_config import PipelineConfigError
```

#### 3. How each message reaches the HTTP 400 body (trace — no HTTP-layer change needed)

The new messages ride the **existing** envelope; this is itself a success criterion. The chain:

1. `validate()` raises `PipelineConfigValidationError((PipelineConfigError(path="", message=…),))`
   — lines 89-92 (over-cap) / 107-113 (too-deep) / 119-121 (unreadable) are the three existing
   precedents the new `except _MergeExpansionTooLarge` clause copies verbatim.
2. `PipelineConfigError` (frozen dataclass) `to_dict()` **omits `line` when `None`** — so the
   merge-bound row is `{"path": "", "message": …}` with no `line`, matching its siblings.

```34:41:backend/src/backend/domain/pipeline_config.py
    path: str
    message: str
    line: int | None = None

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {"path": self.path, "message": self.message}
        if self.line is not None:
            payload["line"] = self.line
        return payload
```

3. `save_pipeline_config(repo, validator, *, yaml_text, …)` calls `validator.validate(yaml_text)`
   **before** `repo.save(...)` — a reject is **zero writes**.
4. The route serialises `exc.errors` into `{"errors": [...]}` at HTTP 400. **Unchanged by this
   phase** — do not touch it.

```577:585:backend/src/backend/interface/http/routes/admin.py
    try:
        config = save_pipeline_config(repo, validator, yaml_text=body.yaml)
    except PipelineConfigValidationError as exc:
        # D-05 / RESEARCH Pitfall 2: top-level {"errors":[...]}, never nested under detail.
        # Repository is not called on reject (D-03/D-07) — zero writes.
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"errors": [error.to_dict() for error in exc.errors]},
        )
```

#### 4. The parse-stage `try` and the `ValidationError` mapping (lines 88-139)

`except _MergeExpansionTooLarge` goes **inside this `try`**, after the `yaml.YAMLError` clause
(D-05: the new pre-pass must not become a new 500 path). The D-07 translation belongs in the
`ValidationError` comprehension at lines 130-139.

```88:139:backend/src/backend/infrastructure/yaml_pipeline_config_validator.py
    def validate(self, yaml_text: str) -> None:
        if len(yaml_text) > MAX_PIPELINE_CONFIG_CHARS:
            raise PipelineConfigValidationError(
                (PipelineConfigError(path="", message=_OVER_CAP_MESSAGE),)
            )

        try:
            data = yaml.load(yaml_text, Loader=_StrictSafeLoader)
        except yaml.MarkedYAMLError as exc:
            mark = exc.problem_mark
            raise PipelineConfigValidationError(
                (
                    PipelineConfigError(
                        path="",
                        line=(mark.line + 1) if mark is not None else None,
                        message=str(exc.problem or exc),
                    ),
                )
            ) from exc
        except RecursionError as exc:
            # WR-02: deeply nested flow collections (< cap) overflow the parser's
            # recursive scanner. Map it to a structured reject at this boundary so
            # the route returns a 400 {"errors":[...]} instead of an unhandled 500.
            raise PipelineConfigValidationError(
                (PipelineConfigError(path="", message=_TOO_DEEP_MESSAGE),)
            ) from exc
        except yaml.YAMLError as exc:
            # CR-01: unmarked YAML errors (e.g. yaml.reader.ReaderError for
            # non-printable/control characters) are yaml.YAMLError but not
            # MarkedYAMLError. Map them to a structured reject too, so user-supplied
            # text never surfaces as an unhandled 500.
            raise PipelineConfigValidationError(
                (PipelineConfigError(path="", message=_UNREADABLE_MESSAGE),)
            ) from exc

        if not isinstance(data, dict) or not all(isinstance(key, str) for key in data):
            raise PipelineConfigValidationError(
                (PipelineConfigError(path="", message=_NOT_A_TEXT_OBJECT_MESSAGE),)
            )

        try:
            PipelineConfigModel.model_validate(data)
        except ValidationError as exc:
            raise PipelineConfigValidationError(
                tuple(
                    PipelineConfigError(
                        path=_loc_to_dot_sep(error["loc"]),
                        message=error["msg"],
                    )
                    for error in exc.errors()
                )
            ) from exc
```

#### 5. The un-touched fixed schema (lines 59-71) — D-01 forbids widening

The projection / `_anchor_holder_keys` must read the allowed-key set from
`PipelineConfigModel.model_fields` (Assumption A5) rather than re-typing the four keys.

```59:71:backend/src/backend/infrastructure/yaml_pipeline_config_validator.py
class PipelineConfigModel(BaseModel):
    """Fixed, documented pipeline-config schema — unknown keys forbidden (D-01/D-02/D-06).

    The four-key set deliberately excludes any secret/credential key (PIPE-03) and
    any ``score_factors`` weight (D-01; ADUX-06 stays on the honest-empty path).
    """

    model_config = ConfigDict(extra="forbid")

    template: Literal["lecture", "podcast"]
    roles: list[Literal["employee", "analyst", "ds"]] = Field(min_length=1)
    language: str = Field(min_length=1)
    max_chars: int = Field(gt=0)
```

#### External reference (NOT a repo analog — read-only, do not edit)

The mechanic the override interposes on lives in the installed PyYAML. This path is **not
git-tracked**; treat it as a library reference for *understanding the shape*, and never as
something the executor edits. The two decisive facts: `node.value = merge + node.value`
(line 213) mutates **in place** (⇒ pristine snapshot needed), and `merge.extend(...)`
(lines 189/202) is the multiplication (⇒ bound needed before `super()`).

```180:218:.venv/Lib/site-packages/yaml/constructor.py
    def flatten_mapping(self, node):
        ...
        if merge:
            node.value = merge + node.value

    def construct_mapping(self, node, deep=False):
        if isinstance(node, MappingNode):
            self.flatten_mapping(node)
        return super().construct_mapping(node, deep=deep)
```

---

### `tests/unit/test_pipeline_config_merge.py` (test, transform — NEW)

**Analog:** `tests/unit/test_pipeline_config_validator.py` — same directory, same import style,
same `pytest` conventions, and it already imports private `_*_MESSAGE` symbols (so importing
`_MERGE_TOO_BIG_MESSAGE` / `_StrictSafeLoader` introduces **no new convention**).

#### Import block + private-symbol convention (lines 1-25)

Mirror this exactly, extending the private-symbol import with the new merge constants and
adding `import yaml` + `import time` (for the bomb's `perf_counter` ceiling). The new module
also imports `PipelineConfigError` for the bound-row equality assertion.

```12:25:tests/unit/test_pipeline_config_validator.py
from __future__ import annotations

import sys

import pytest

from backend.domain.errors import PipelineConfigValidationError
from backend.domain.pipeline_config import PipelineConfigError
from backend.infrastructure.yaml_pipeline_config_validator import (
    MAX_PIPELINE_CONFIG_CHARS,
    PipelineConfigModel,
    YamlPipelineConfigValidator,
    _TOO_DEEP_MESSAGE,
    _UNREADABLE_MESSAGE,
)
```

#### The `_errors()` harness to copy (lines 28-32)

Every existing reject assertion goes through this helper. The new module reuses the identical
shape (one per module — no shared `conftest.py` exists).

```28:32:tests/unit/test_pipeline_config_validator.py
def _errors(yaml_text: str) -> tuple[PipelineConfigError, ...]:
    validator = YamlPipelineConfigValidator()
    with pytest.raises(PipelineConfigValidationError) as exc_info:
        validator.validate(yaml_text)
    return exc_info.value.errors
```

#### The valid-config builder to reuse (REQUIREMENT: guidance #5)

There is **no shared builder function** — the existing convention is a **module-level YAML
string constant**. `VALID_DOC` (line 25) is the closest thing to "builds a valid config
document"; the HTTP tests use inline strings of the same shape. The new module must follow this
constant pattern (its own `VALID_DOC`, `ORACLE_ACCEPTED`, `SCHEMA_ACCEPTED`,
`DUPLICATE_REJECTED`, bomb fixtures) rather than invent a builder, since no other module
exports one.

```25:25:tests/unit/test_pipeline_config_validator.py
VALID_DOC = "template: lecture\nroles:\n  - employee\nlanguage: ru\nmax_chars: 4000\n"
```

#### Duplicate-reject shape to preserve (lines 61-69)

The merge module's Group 3 (`DUPLICATE_REJECTED`, with and without a `<<`) must assert the same
three facts — one error, `"duplicate"` in the lowercase message, mark-derived `line`.

```61:69:tests/unit/test_pipeline_config_validator.py
def test_duplicate_top_level_key_is_rejected_not_last_wins() -> None:
    """RED→GREEN: SafeLoader last-wins is replaced by a strict duplicate reject."""
    errors = _errors(
        "template: podcast\ntemplate: lecture\nroles:\n  - ds\nlanguage: ru\nmax_chars: 100\n"
    )

    assert len(errors) == 1
    assert "duplicate" in errors[0].message.lower()
    assert errors[0].line == 2
```

#### Structured-reject row shape for the new bound test (lines 207-226)

The bomb test's exact-reject assertion follows the same pattern: one error, `path == ""`,
`line is None`, `message == <constant>`. It additionally asserts
`_MERGE_TOO_BIG_MESSAGE != _OVER_CAP_MESSAGE` (D-06) and a `time.perf_counter()` ceiling
(~0.5 s vs ~1.5 s unbounded — Pitfall 7 / Q9). Do **not** use `pytest-timeout` (not installed)
or `SIGALRM` (unavailable on win32).

```207:226:tests/unit/test_pipeline_config_validator.py
def test_deeply_nested_flow_document_is_rejected_not_recursion_error() -> None:
    """RED→GREEN WR-02: nested flow brackets (under the cap) → structured error.

    Before the fix the parser raises an unhandled ``RecursionError`` (HTTP 500);
    strict validation must instead map it to a ``PipelineConfigValidationError``.
    The depth is derived from the live recursion limit (plus a margin) so the test
    keeps exercising the overflow branch even if the limit is raised.
    """
    depth = sys.getrecursionlimit() + 500
    document = ("[" * depth) + ("]" * depth)

    assert len(document) <= MAX_PIPELINE_CONFIG_CHARS

    errors = _errors(document)

    assert len(errors) == 1
    assert errors[0].path == ""
    assert errors[0].line is None
    assert errors[0].message == _TOO_DEEP_MESSAGE
```

#### Oracle loop (the new pattern that makes the corpus the contract)

No analog exists for the `yaml.SafeLoader`-as-oracle loop — it is this phase's new test idea.
Shape it as a `@pytest.mark.parametrize` over module-level string tuples, per Q4:

```python
@pytest.mark.parametrize("document", ORACLE_ACCEPTED)
def test_strict_loader_matches_safeloader_oracle(document: str) -> None:
    assert yaml.load(document, Loader=_StrictSafeLoader) == yaml.safe_load(document)
```

---

### `tests/unit/test_http_pipeline_config.py` (test, request-response — MODIFIED, +1 test)

**Analog:** itself. The new merge round-trip test copies `_real_validator_admin_env()` +
`test_put_then_get_round_trip_returns_saved_yaml` for the accept path, and
`test_put_invalid_error_rows_are_verbatim_and_top_level` for the (optional) HTTP-level zero-write
proof.

#### The real-validator harness to reuse (lines 129-142)

This is exactly the fixture that wires the **real** `YamlPipelineConfigValidator` (vs. the
accept-all `InMemoryPipelineConfigValidator` that `_admin_env()` attaches). The new test must
call this one — do not build a new harness.

```129:142:tests/unit/test_http_pipeline_config.py
def _real_validator_admin_env() -> tuple[TestClient, dict[str, str], Any]:
    """Admin client on the default wiring: real YamlPipelineConfigValidator + recording repo."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    container = build_in_memory_container()
    _seed_profile(
        container,
        user_id="admin-uuid-1",
        email="admin@sberbank.ru",
        role="admin",
    )
    client = _client(jwk, container)
    token = _mint(private_key, email="admin@sberbank.ru", sub="admin-uuid-1")
    return client, {"Authorization": f"Bearer {token}"}, container
```

#### The 4-key PUT/GET round-trip to copy (lines 174-192)

The new merge test is this exact assertion with a merge-key `yaml_text`:
PUT → 200 → body `yaml` identical → `updated_at` non-null → GET returns the identical `yaml`
(the "reads back in a later session" criterion, PIPE-04). It uses `_admin_env()` (accept-all
validator); the **merge variant must use `_real_validator_admin_env()`** so the merge actually
flows through the strict loader.

```174:192:tests/unit/test_http_pipeline_config.py
def test_put_then_get_round_trip_returns_saved_yaml() -> None:
    """PIPE-01/PIPE-03, D-11: PUT a valid document, then GET returns the identical yaml."""
    yaml_text = "template: lecture\nroles:\n  - employee\nlanguage: ru\nmax_chars: 4000\n"
    client, headers, container = _admin_env(config=None)

    put = client.put(CONFIG_URL, headers=headers, json={"yaml": yaml_text})

    assert put.status_code == 200
    put_body = put.json()
    assert set(put_body.keys()) == {"yaml", "updated_at"}
    assert put_body["yaml"] == yaml_text
    assert put_body["updated_at"] is not None
    # The validator port ran before the write (validate-then-persist).
    assert container.pipeline_config_validator.calls == [yaml_text]

    get = client.get(CONFIG_URL, headers=headers)

    assert get.status_code == 200
    assert get.json()["yaml"] == yaml_text
```

> Note: with `_real_validator_admin_env()` the container's validator is the real
> `YamlPipelineConfigValidator`, which has **no `.calls` list** — so the merge test asserts the
> round-trip and (if desired) `container.pipeline_config.save_count == 0` on the reject path,
> **not** `.calls == [...]`. The `.calls` assertion is specific to the `_admin_env()` fake
> (`InMemoryPipelineConfigValidator.calls`, `tests_support/in_memory.py:653-660`).

#### The D-09 tripwire to PRESERVE untouched (lines 285-307)

Byte-identical rows for a **non-merge** document → `_anchor_holder_keys` returns ∅ → the English
`extra_forbidden` message survives. **Do not modify this test.** It is the reason the D-07
translation must be gated on anchor identity rather than applied to every extra key.

```285:307:tests/unit/test_http_pipeline_config.py
def test_put_invalid_error_rows_are_verbatim_and_top_level() -> None:
    """RED→GREEN D-05: error rows expose path/message (+ optional line), verbatim server text."""
    client, headers, container = _real_validator_admin_env()
    document = (
        "template: lecture\nroles:\n  - ds\nlanguage: ru\nmax_chars: 100\nscore_factors: 1.0\n"
    )
    try:
        YamlPipelineConfigValidator().validate(document)
        raise AssertionError("expected the validator to reject the unknown key")
    except PipelineConfigValidationError as exc:
        expected = [error.to_dict() for error in exc.errors]

    response = client.put(CONFIG_URL, headers=headers, json={"yaml": document})

    assert response.status_code == 400
    body = response.json()
    assert "detail" not in body
    assert body["errors"] == expected
    row = body["errors"][0]
    assert set(row.keys()) <= {"path", "message", "line"}
    assert row["path"] == "score_factors"
    assert "line" not in row
    assert container.pipeline_config.save_count == 0
```

#### Sibling message-only row shapes (lines 310-343) — the merge-bound row follows these

If the plan adds an HTTP-level bomb test (optional; the unit test is primary), assert the row as
`body["errors"] == [{"path": "", "message": _MERGE_TOO_BIG_MESSAGE}]` and
`container.pipeline_config.save_count == 0`, exactly as these two do.

```310:326:tests/unit/test_http_pipeline_config.py
def test_put_deeply_nested_yaml_returns_400_not_500() -> None:
    """RED→GREEN WR-02: deeply nested flow collections → structured 400, never an unhandled 500."""
    client, headers, container = _real_validator_admin_env()
    depth = sys.getrecursionlimit() + 500
    document = ("[" * depth) + ("]" * depth)

    response = client.put(CONFIG_URL, headers=headers, json={"yaml": document})

    assert response.status_code == 400
    body = response.json()
    assert "detail" not in body
    assert body["errors"] == [
        {"path": "", "message": _TOO_DEEP_MESSAGE}
    ]
    # The reject never reached the repository (D-03/D-07): zero saves.
    assert container.pipeline_config.save_count == 0
```

#### Import block to extend (lines 28-32)

Add `_MERGE_TOO_BIG_MESSAGE` (and `_OVER_CAP_MESSAGE` if the bomb test asserts the `!=`)
to this existing project-import block.

```28:32:tests/unit/test_http_pipeline_config.py
from backend.infrastructure.yaml_pipeline_config_validator import (
    YamlPipelineConfigValidator,
    _TOO_DEEP_MESSAGE,
    _UNREADABLE_MESSAGE,
)
```

---

## Shared Patterns

### Structured-reject envelope (path/message, `line` omitted when None)
**Source:** `backend/src/backend/domain/pipeline_config.py` `PipelineConfigError.to_dict()` (lines 34-41)
**Apply to:** the merge-bound reject (`path=""`, no `line`) and the D-07 anchor-holder row (loc-derived `path`, no `line`)
```python
# PipelineConfigError(path="", message=_MERGE_TOO_BIG_MESSAGE).to_dict()
{"path": "", "message": "Документ содержит слияние (merge), превышающее допустимый размер"}
```

### Adapter-boundary error mapping (never a new 500 path — D-05 / WR-02 / CR-01)
**Source:** `yaml_pipeline_config_validator.py:94-121` (`MarkedYAMLError` / `RecursionError` / `yaml.YAMLError` clauses)
**Apply to:** the new `except _MergeExpansionTooLarge` clause (inside the same `try`) and the D-07 `yaml.compose()` helper (wrap in `except (yaml.YAMLError, RecursionError) -> set()`)
```python
        except _MergeExpansionTooLarge as exc:
            raise PipelineConfigValidationError(
                (PipelineConfigError(path="", message=_MERGE_TOO_BIG_MESSAGE),)
            ) from exc
```

### Private-symbol imports in unit tests
**Source:** `tests/unit/test_pipeline_config_validator.py:17-23` and `tests/unit/test_http_pipeline_config.py:28-32`
**Apply to:** the new merge test module
```python
from backend.infrastructure.yaml_pipeline_config_validator import (
    _MERGE_TOO_BIG_MESSAGE,
    _StrictSafeLoader,
)
```

### Validate-before-save with zero writes (PIPE-02)
**Source:** `application/use_cases/pipeline_config.py` + route at `admin.py:577-585`
**Apply to:** every merge reject test at the HTTP level — assert `container.pipeline_config.save_count == 0`

---

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| (none) | — | — | All three files have an exact or self analog. |

**New patterns with no codebase precedent** (still no *file* lacking an analog — these are
test-construction techniques the planner should source from `17-RESEARCH.md` § Q4/Q9, not from
existing repo code):
- the `yaml.SafeLoader`-as-oracle parametrized loop,
- the `time.perf_counter()` bounded-time ceiling,
- the `_anchor_holder_keys` / `_project` helpers inside the adapter (no peer helper exists).

---

## Metadata

**Analog search scope:** `backend/src/backend/infrastructure/`, `backend/src/backend/domain/`,
`backend/src/backend/application/`, `backend/src/backend/interface/http/routes/`, `tests/unit/`,
`backend/src/backend/tests_support/` (plus `pyproject.toml` for pytest config, and repo-wide
`git ls-files` for the tracked-source gate)
**Files scanned:** 8 read in full/targeted (`yaml_pipeline_config_validator.py`,
`test_pipeline_config_validator.py`, `test_http_pipeline_config.py`, `pipeline_config.py` (domain),
`errors.py`, `ports/pipeline_config.py`, `admin.py` excerpt, `tests_support/in_memory.py` excerpt)
+ repo-wide glob/grep for analogs and `conftest.py`
**Pattern extraction date:** 2026-10-14

**Key structural findings for the planner:**
1. The only production diff is `yaml_pipeline_config_validator.py`; its input shape to preserve is the
   existing `construct_mapping` override at lines 36-56 — the new `flatten_mapping` override mirrors it
   (`super()` delegation, `ConstructorError` with both marks, module-level `_*_MESSAGE` constants).
2. New messages need **zero** HTTP-layer change: `PipelineConfigError.to_dict()` → route serializer
   at `admin.py:577-585` already carries them.
3. `tests/unit/test_pipeline_config_merge.py` does **not** exist (confirming it is the Wave-0 RED module);
   it copies `test_pipeline_config_validator.py`'s imports, `_errors()` helper and reject-row assertions.
4. No `conftest.py` exists anywhere → the new module owns its module-level YAML-string constants; there is
   no shared "valid config builder" to reuse beyond the `VALID_DOC`-style constant convention.
5. The HTTP round-trip must use `_real_validator_admin_env()` (real validator), not `_admin_env()` (fake);
   the `.calls == [...]` assertion from the existing round-trip test does **not** apply to the real validator.
6. `test_put_invalid_error_rows_are_verbatim_and_top_level` (lines 285-307) is the D-09 tripwire — PRESERVE.
