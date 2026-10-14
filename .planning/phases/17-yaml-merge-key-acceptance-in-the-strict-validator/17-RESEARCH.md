# Phase 17: YAML merge-key acceptance in the strict validator - Research

**Researched:** 2026-10-14
**Domain:** PyYAML `SafeLoader` subclassing · YAML merge-key (`<<`) semantics · bounded-parse DoS defence
**Confidence:** HIGH — every mechanic below was reproduced on this checkout against the repo's own interpreter (`.venv`: CPython **3.12.13**, PyYAML **6.0.3**, pytest **9.1.1**). Nothing here is derived from training memory.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** The fix is confined to the parse path; the locked 4-key `extra="forbid"` schema is **not** widened. A merge document is accepted only when the merge resolves to exactly those four keys (verified shapes: `<<: &base` + 4 keys, and `<<: &base` + an explicit local override). The natural anchor-holder style (`defaults: &base` + `<<: *base`) stays rejected — but now with an honest, teachable error instead of a cryptic one. — **Reversibility:** one-way — widening the schema later changes which documents are accepted, i.e. a published behaviour contract (PIPE-02's validate-before-save envelope plus the v1.2 decisions D-01/D-02/D-06 that fixed the four-key set), not a local edit. User's rationale, recorded verbatim: *"Только фикс парсинга, схема нетронута"*.
- **D-02:** Duplicate detection stays on the **pre-merge own-key list**; the merge key node is skipped by its tag `tag:yaml.org,2002:merge`, **never** by matching the literal string `'<<'` (a quoted `'<<'` is an ordinary key). Explicit duplicate keys keep producing the same verbatim top-level structured 400 `{errors:[…]}` with zero writes. — **Reversibility:** costly — the scan order is PIPE-02's contract and is pinned by `test_put_invalid_error_rows_are_verbatim_and_top_level`; `flatten_mapping` must never move above the `seen` loop (Pitfall 7).
- **D-03:** Collisions introduced **by** merge follow the YAML spec and are **not** errors: the first merge source wins, and an explicit own key overrides a merged key. Only explicit own-key duplicates are rejected, so `<<: *base` plus a local overriding key is a legitimate document and must load with the local value winning. User's rationale: *"Строгость к явным дубликатам неизменна"* — merge-introduced collisions are override semantics, not mistakes.
- **D-04:** Two independent bounds, **both enforced before the expensive flatten step**: (a) merge depth / fan-out, and (b) a total budget of materialised (flattened) entries. Defence in depth, so no legitimate document is refused by a single crude metric. — **Reversibility:** costly — the bound is the only thing standing between the fix and a newly reachable DoS; loosening it later re-opens the CPU path. Measured evidence on this checkout: **457 chars → 5.26 s**, cost ≈ **×3 per extra level** (levels 12/13/14 → 0.70 s / 1.87 s / 5.26 s), i.e. ~15 s at level 15 and ~45 s at level 16 — all far inside the 20 000-char source cap. User's rationale: *"И глубина/fan-out слияний, и общий бюджет развёрнутых пар — и отказ ДО тяжёлой работы"*.
- **D-05:** Any new pre-pass (`yaml.compose` / node walk) is wrapped in the **same** `RecursionError` + `yaml.YAMLError` mapping the loader already has, so a new pre-pass cannot become a new 500 path (WR-02 / CR-01 contract from Phase 16).
- **D-06:** A **new dedicated** Russian message for the merge bound: «Документ содержит слияние (merge), превышающее допустимый размер». It must **not** reuse `_OVER_CAP_MESSAGE` («Документ конфига превышает допустимый размер»), because a merge-bomb document is ~500 characters — claiming it exceeds the size cap would be false. Same envelope as its siblings: top-level `{errors:[{path:"", message}]}`, zero writes. User's rationale: *"документ ~500 символов, говорить «превышает размер» было бы ложью"*.
- **D-07:** An extra top-level anchor-holder key gets its own Russian message that **teaches the correct form**, naming the offending key — canonical wording: «Лишний ключ «defaults»: якоря нужно объявлять в самом `<<`» (the key name is interpolated from the document). Rationale: under D-01 this is *the most likely* admin mistake after the fix (anyone wanting reuse writes `defaults:`/`common:`/`base:`), and leaving it as Pydantic's English «Extra inputs are not permitted» would reintroduce exactly the cryptic error this phase exists to remove. User's rationale: *"иначе самый частый сценарий остаётся криптовым"*.
- **D-08:** No editor hint in this phase. A hint advertising `<<` support would be dishonest while anchor reuse does not work (D-01). Recorded as a backlog item instead of scope. User's rationale: *"минимальный скоуп и никакой лживой подсказки, пока переиспользование не работает"*.
- **D-09:** `test_put_invalid_error_rows_are_verbatim_and_top_level` → **PRESERVE**. The reject envelope must be byte-identical after the fix. No test currently asserts merge behaviour, so no existing merge test needs amending (confirmed by grep on `tests/unit/test_pipeline_config_validator.py`).

### Claude's Discretion

- The numeric values of both bounds (depth/fan-out limit and flattened-entry budget), as long as a legitimate 4-key config is never refused and the measured bomb shape is refused fast.
- Pre-pass mechanics: `yaml.compose` + node walk vs. a counting `construct_mapping` — whichever keeps the cost out of the flatten step.
- Where the new constants and message strings live (alongside `MAX_PIPELINE_CONFIG_CHARS` and the existing `_*_MESSAGE` constants is the natural home).
- Test organisation: new module vs. additions to `tests/unit/test_pipeline_config_validator.py`; the `yaml.SafeLoader` oracle loop is required either way.

### Deferred Ideas (OUT OF SCOPE)

- **Editor hint about `<<` support** — a hint next to the raw YAML editor saying merge keys are supported. Deferred because it would advertise a capability that anchor reuse (D-01) does not actually deliver; it becomes honest only if the schema is ever widened. **Candidate backlog item** for `/gsd-review-backlog`; would need a UI-SPEC touch (`16-UI-SPEC.md` A-1 editor section) plus a Playwright RED test if ever picked up.

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PIPE-04 | The strict pipeline-config validator accepts a valid YAML merge-key (`<<`) document and persists it, while still rejecting duplicate **explicit** keys with the same top-level structured 400 `{errors:[…]}` and zero writes | Q1–Q4. Verified: `<<: &base` + own keys and `<<: &base` + explicit override both load and resolve to exactly the 4 schema keys; the loader-level oracle matches `yaml.SafeLoader` on **74** schema-accepted merge probes with **0** mismatches; explicit duplicates (with and without a `<<`) still raise `found duplicate key (...)` with identical marks. |
| PIPE-05 | Merge expansion is bounded so a small document cannot exhaust CPU (breach returns the structured 400), and duplicate-key rejection is provably not weakened | Q5, Q6, Q9 (+Q3 for the duplicate proof). Verified: the memoised `(entries, depth)` projection at the head of `flatten_mapping` refuses every measured bomb in **~2 ms** (vs **0.5–4.3 s** unbounded at 445–515 chars), while a legitimate 4-key merge costs **1.2 µs** of projection; duplicate rejection is pinned by the preserved tripwire plus a new merge-present duplicate case. |

</phase_requirements>

## Summary

The phase is a **pure parse-path fix inside one adapter**. The failure is fully reproduced on this checkout: `_StrictSafeLoader.construct_mapping` constructs **every** key node *before* `SafeConstructor.flatten_mapping` ever runs, and the merge key node carries `tag:yaml.org,2002:merge`, for which PyYAML registers **no** constructor — so a valid `<<` document dies with `ConstructorError: could not determine a constructor for the tag 'tag:yaml.org,2002:merge'`.

The interesting part — the part `PITFALLS.md` does not contain — is that the obvious fix (`continue` on the merge tag, delegate to `super()`) is **not sufficient**, for a reason that is invisible unless you construct the trap. `SafeConstructor.flatten_mapping` mutates `MappingNode.value` **in place** (`node.value = merge + node.value`, `constructor.py:213`). A mapping that a parent already flattened and that is *also* constructed as an object (the `defaults: &base` + `<<: *base` anchor-holder idiom — precisely D-07's shape) is later scanned by its own `construct_mapping` over the **already-expanded** list, so merge-introduced collisions are reported as `found duplicate key ('roles')` — a D-03 violation and an oracle failure. Reproduced: with the skip-only loader, `defaults: &c` + `<<: [&a {roles: [ds]}, &b {roles: [analyst]}]` + `<<: *c` raises `found duplicate key ('roles')` where `SafeLoader` returns a clean mapping. The fix therefore needs **two** small pieces, not one: (1) skip the merge tag in the scan, and (2) scan the **pristine own-key list**, snapshotted in a new `flatten_mapping` override at the one moment a node is guaranteed un-mutated.

The second half of the phase is the bound. Once merges work, `flatten_mapping` is reachable and multiplies the node list (`k^depth`); **measured on this checkout**, a fan-out-3 chain costs 1.9 ms at 253 chars, 63 ms at 375, 503 ms at 445, 1.5 s at 480 and **4.3 s at 515 chars** — all far inside the 20 000-char cap. A memoised `(entries, depth)` projection computed at the head of the same `flatten_mapping` override — **before** `super().flatten_mapping(node)` — refuses every one of those bombs in ~2 ms and costs **1.2 µs** on a legitimate merge document.

**Primary recommendation:** keep `_StrictSafeLoader` a `SafeLoader` subclass. Edit `construct_mapping` to `continue` on `key_node.tag == _MERGE_TAG` and to scan the **pristine** own-key list; **add** a `flatten_mapping` override that (once per node) snapshots the pristine own keys and, when a merge key is present, runs a memoised `(entries, depth)` projection that raises a private `_MergeExpansionTooLarge` before `super()`. Map that exception in `validate()` to `_MERGE_TOO_BIG_MESSAGE` (`path=""`, `line` omitted). Translate the Pydantic `extra_forbidden` message **only** for top-level keys identified as merge-anchor holders by a guarded `yaml.compose()` on the reject path. Ship RED pytest tests: a `yaml.SafeLoader` oracle corpus, an accept/round-trip test, a bomb test asserting the structured reject *and* bounded time, and the preserved `test_put_invalid_error_rows_are_verbatim_and_top_level` tripwire. **No HTTP-layer or composition change.**

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Accept a valid `<<` merge document | API / Backend (infrastructure adapter) | — | The parse gate is server-authoritative (PIPE-02); the SPA sends raw YAML verbatim and never inspects it. |
| Reject explicit duplicate keys (unchanged) | API / Backend (infrastructure adapter) | — | Duplicate detection lives in `_StrictSafeLoader.construct_mapping`; it is a parse concern, not a schema concern. |
| Bound merge expansion before flatten | API / Backend (infrastructure adapter) | — | Only the loader holds the composed node graph, and the reject must happen before `flatten_mapping` materialises the expanded list. |
| Map rejects to the structured 400 `{errors:[…]}` | API / Backend (HTTP route) | — | `put_pipeline_config` already serialises `PipelineConfigError.to_dict()`; **no change needed** (D-06/D-07 ride the existing envelope). |
| Teach the anchor-holder mistake (D-07) | API / Backend (infrastructure adapter) | — | Pydantic's `extra_forbidden` message is produced inside `validate()`; anchor identity exists only in the parse-time node graph. |
| Persist and read back the merge document | Database / Storage | — | `repo.save(yaml=...)` stores the raw text; the merge is expanded only at validation time, never at write time. |
| Editor hint about `<<` | Browser / Client | — | **Deferred (D-08).** Not in this phase. |

## Standard Stack

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyYAML (`yaml`) | **6.0.3** — `[VERIFIED: .venv]` (`.venv\Scripts\python.exe -c "import yaml; print(yaml.__version__)"` → `6.0.3`) | The only YAML parser in the repo; `_StrictSafeLoader` subclasses `yaml.SafeLoader` | `SafeLoader` is the safe-by-default loader; merge keys are a native `SafeLoader` feature that only this project's duplicate-key override breaks. Pitfall 9 forbids changing the `Loader=` argument or the class hierarchy, and forbids `yaml.safe_load`/`FullLoader`. |
| Pydantic | 2.13 (`[VERIFIED: .venv]` — error payload carries `https://errors.pydantic.dev/2.13/v/extra_forbidden`) | The fixed 4-key `extra="forbid"` schema | Existing schema; D-01 forbids widening it. Produces the `extra_forbidden` error D-07 translates. |
| pytest | **9.1.1** — `[VERIFIED: .venv]` (`.venv\Scripts\python.exe -m pytest --version` → `pytest 9.1.1`) | Unit tests for the adapter | Config lives in `pyproject.toml` `[tool.pytest.ini_options]`, `testpaths = ["tests/unit"]`, `pythonpath = ["."]`. |
| CPython | **3.12.13** — `[VERIFIED: .venv]`; `requires-python = ">=3.12"` in `pyproject.toml` | Runtime | Note: `PITFALLS.md` measured on CPython **3.14.0** (a different interpreter); semantics are identical, timings differ by a factor ≈2 (see Q6). |

**No new dependencies.** This phase adds zero packages: the whole diff is `backend/src/backend/infrastructure/yaml_pipeline_config_validator.py` plus pytest files.

## Package Legitimacy Audit

**Not applicable — this phase installs no external packages.** `pyyaml==6.0.3` is already resolvable in `pyproject.toml`/`uv.lock` and present in `.venv`; Pydantic and pytest are already dependencies. There is no `npm`/`pip`/`cargo` install step in this phase, so the Package Legitimacy Gate is skipped by design. **Packages removed due to [SLOP] verdict:** none. **Packages flagged as suspicious [SUS]:** none.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python (`.venv`) | everything | ✓ | 3.12.13 | — |
| PyYAML | the adapter under change | ✓ | 6.0.3 | — |
| pytest | RED→GREEN tests | ✓ | 9.1.1 | — |
| pytest-timeout | flaky-proof timing assertions | ✗ | — | **Use a `time.perf_counter()` ceiling with a ≥100× margin, or a call-count spy.** `[VERIFIED: .venv]` — `importlib.util.find_spec("pytest_timeout")` → `None`. |
| `signal.alarm` | hard test timeouts | ✗ (Windows, `os.name == 'nt'`) | — | Do **not** rely on `SIGALRM`; the project runs on win32. |

**Missing dependencies with no fallback:** none — the phase is a pure code change.
**Missing dependencies with fallback:** `pytest-timeout` (use a generous `perf_counter` ceiling instead, sized so an unbounded regression fails in ~1.5 s instead of hanging — Q9).

## Architecture Patterns

### System Architecture Diagram

```text
 admin SPA (raw YAML text, verbatim)
        │  PUT /admin/pipeline/config  {"yaml": "..."}
        ▼
 HTTP route  backend/interface/http/routes/admin.py  (UNCHANGED)
        │  save_pipeline_config(repo, validator, yaml_text=…)
        ▼
 use case   backend/application/use_cases/pipeline_config.py
        │        validator.validate(yaml_text)      ◀── validate BEFORE any write
        ▼
 YamlPipelineConfigValidator.validate()          ← the ONLY file that changes
        │
        ├─ 1. len(yaml_text) > MAX_PIPELINE_CONFIG_CHARS ──▶ 400 «…превышает допустимый размер»
        │
        ├─ 2. yaml.load(text, Loader=_StrictSafeLoader)
        │         │
        │         ├─ Scanner/Parser/Composer  ──▶ SyntaxError/ComposerError ─┐
        │         ├─ RecursionError (deep flow) ──▶ _TOO_DEEP_MESSAGE        ├─▶ 400 {errors:[…]}
        │         ├─ yaml.YAMLError (ReaderError) ──▶ _UNREADABLE_MESSAGE    │
        │         └─ construction:
        │              construct_object(root)
        │                → construct_yaml_map(root)          (generator)
        │                → _StrictSafeLoader.construct_mapping(root)
        │                     ├─ NEW: scan PRISTINE own-key list, skip _MERGE_TAG
        │                     │        dup? ──▶ ConstructorError «found duplicate key (…)»  ──┐
        │                     └─ super() → SafeConstructor.construct_mapping(root)
        │                            └─ _StrictSafeLoader.flatten_mapping(root)   ◀── NEW override
        │                                   ├─ snapshot pristine own keys (once per node)
        │                                   └─ merge present?  project(entries, depth)
        │                                          over budget? ──▶ _MergeExpansionTooLarge ─┐
        │                                   └─ super().flatten_mapping(node) ── materialises k^depth
        │
        ├─ 3. data must be a dict of str keys ──▶ _NOT_A_TEXT_OBJECT_MESSAGE
        │
        └─ 4. PipelineConfigModel.model_validate(data)   (extra="forbid", 4 keys)
                 ├─ extra_forbidden on an ANCHOR-HOLDER key (NEW, guarded yaml.compose)
                 │        ──▶ 400 «Лишний ключ «defaults»: якоря нужно объявлять в самом `<<`»
                 └─ any other error ──▶ 400 {errors:[{path, message}…]}

                     ▼
   repository.save(yaml=…)   ── reached ONLY when validate() returns; a reject is ZERO WRITES
```

The only boxes that change are the two inside `YamlPipelineConfigValidator.validate()` / `_StrictSafeLoader`. The HTTP route, the use case, the port, the domain model and the repository are untouched.

### Recommended Project Structure

No new production modules — the fix stays inside the existing adapter:

```text
backend/src/backend/infrastructure/
└── yaml_pipeline_config_validator.py   # constants + _StrictSafeLoader + validate() (the whole diff)

tests/unit/
├── test_pipeline_config_validator.py   # 16 existing tests — PRESERVE (tripwire lives in the HTTP file)
├── test_http_pipeline_config.py        # 13 existing tests — PRESERVE, +1 merge round-trip
└── test_pipeline_config_merge.py       # NEW: oracle corpus + bound + D-07 RED tests
```

### Pattern 1: Subclass-the-safe-loader, never re-plumb the loader

**What:** `_StrictSafeLoader` overrides two methods of `yaml.SafeLoader` (`construct_mapping`, `flatten_mapping`) and always delegates with `super()`. The class must remain a `SafeLoader` subclass and `validate()` must keep passing `Loader=_StrictSafeLoader`.
**When to use:** always, for this file.
**Why:** `SafeLoader` registers `None → construct_undefined` (`constructor.py:479-480`), so *any* unknown tag — including the merge tag — fails closed. `yaml.safe_load` would delete the duplicate-key contract; `FullLoader`/no `Loader=` re-opens arbitrary object construction (Pitfall 9).

```python
# Source: .venv/Lib/site-packages/yaml/constructor.py (verbatim structure of the base methods)
class SafeConstructor(BaseConstructor):
    def flatten_mapping(self, node):        # line 180 — mutates node.value IN PLACE
        ...
        if merge:
            node.value = merge + node.value  # line 213

    def construct_mapping(self, node, deep=False):   # line 216
        if isinstance(node, MappingNode):
            self.flatten_mapping(node)              # ← runs *after* our scan, via super()
        return super().construct_mapping(node, deep=deep)
```

### Pattern 2: pristine snapshot + memoised projection at the head of an override

**What:** our `flatten_mapping` override does its bookkeeping **before** `return super().flatten_mapping(node)`, which is the only window where `node.value` is guaranteed un-mutated for that node.
**When to use:** exactly once, in this adapter.
**Why:** it gives both the correctness fix (pristine own keys for the duplicate scan) and the DoS bound (projected `(entries, depth)`) from a single hook, with no second parse.

```python
# Design sketch — verified to satisfy the oracle corpus and refuse every measured bomb
_MERGE_TAG = "tag:yaml.org,2002:merge"
MAX_MERGE_DEPTH = 8
MAX_MERGE_ENTRIES = 256


def flatten_mapping(self, node: MappingNode) -> None:
    if isinstance(node, MappingNode) and id(node) not in self._checked:
        self._checked.add(id(node))
        if any(key_node.tag == _MERGE_TAG for key_node, _ in node.value):
            self._own_keys[id(node)] = list(node.value)   # pristine, merge tag still present
            _project(node, self._memo, set())              # raises before any expansion
    return super().flatten_mapping(node)


def construct_mapping(self, node: MappingNode, deep: bool = False) -> dict[Any, Any]:
    if isinstance(node, MappingNode):
        seen: set[Any] = set()
        for key_node, _value_node in self._own_keys.get(id(node), node.value):
            if key_node.tag == _MERGE_TAG:          # D-02: by tag, never by the literal '<<'
                continue
            key = self.construct_object(key_node, deep=deep)
            ...
    return super().construct_mapping(node, deep=deep)
```

### Anti-Patterns to Avoid

- **Scanning *after* `flatten_mapping`:** `node.value = merge + node.value` makes merged pairs look like duplicates, so a valid local-over-merged override is rejected (Pitfall 7). Reproduced: the flatten-then-scan loader raises `found duplicate key ('y')` for a document `SafeLoader` happily resolves to `{'x': 1, 'y': 3}`.
- **Matching the literal string `'<<'`:** a quoted `'<<'` key keeps tag `tag:yaml.org,2002:str` and must stay an ordinary key (D-02). Verified with `yaml.compose`.
- **Skipping the merge tag without adding a bound:** `flatten_mapping` becomes reachable and multiplies the node list — a 445-char document already costs 503 ms, a 515-char one 4.3 s (Pitfall 8, re-measured here).
- **A separate `yaml.compose()` pre-pass on the happy path:** a second loader instantiation + second parse per save (~200 µs), for no gain over the in-loader hook. Keep `yaml.compose()` for the D-07 reject path only.
- **Raising the merge-bound reject as a `ConstructorError`:** it is a `MarkedYAMLError`, so the existing branch attaches a `line`, and the row stops matching the sibling `{"path": "", "message": …}` envelope.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML parsing / merge semantics | A regex/line-based `<<` rewriter before parsing | `yaml.SafeLoader`'s own `flatten_mapping` | Merge semantics (first source wins, sequence sources, `!!merge`, quoted `'<<'`) are subtle; reimplementing them will diverge from the spec and from `SafeLoader`, which is the phase's oracle. |
| Duplicate-key detection | A text scan for repeated `key:` prefixes | The existing `construct_object`-based `seen` loop | It must understand tags, quoting and non-string keys.
| "How big will the merge get?" | Counting characters, or counting entries inside `flatten_mapping` | A memoised node-graph projection before `super().flatten_mapping` | Character count misses amplification (a bomb is ~500 chars); counting inside flatten observes the expansion only after the work is already done (Q5). |
| Structured-400 envelope | Any new response shape or a new HTTP branch | `PipelineConfigError(path, message).to_dict()` through the existing route | D-06/D-07 are message-only changes; the envelope is a pinned contract. |

**Key insight:** in this domain the *loader is the oracle*. Anything hand-rolled has to reproduce `SafeLoader`'s merge semantics exactly — so the cheapest correct design is to let `SafeLoader` do the merging and to interpose only two narrow hooks around it.

## Research Question Answers

All line numbers below are from this checkout; PyYAML paths are `.venv/Lib/site-packages/yaml/constructor.py`.

### Q1 — Exact mechanic of the correct fix

**The chain (verbatim from the installed PyYAML):**

| Step | Location | What happens |
|---|---|---|
| 1 | `BaseConstructor.construct_object` `constructor.py:66-116` | Looks up `self.yaml_constructors[node.tag]`; no multi-constructor matches; `None in self.yaml_constructors` is **True** (registered at `constructor.py:479-480`) → `constructor = construct_undefined`. |
| 2 | `SafeConstructor.construct_yaml_map` `constructor.py:411-414` | A **generator**: `data = {}` → `yield data` → `value = self.construct_mapping(node)` → `data.update(value)`. |
| 3 | `_StrictSafeLoader.construct_mapping` (ours, `yaml_pipeline_config_validator.py:39-56`) | The `seen` loop runs **first**, calling `self.construct_object(key_node, deep=deep)` for **every** key node — including the merge key node. |
| 4 | `construct_undefined` `constructor.py:426-429` | `raise ConstructorError(None, None, "could not determine a constructor for the tag %r" % node.tag, node.start_mark)` — the cryptic failure. |
| 5 | `SafeConstructor.construct_mapping` `constructor.py:216-219` | Only *after* our scan: `if isinstance(node, MappingNode): self.flatten_mapping(node)` then `return super().construct_mapping(node, deep=deep)`. |
| 6 | `SafeConstructor.flatten_mapping` `constructor.py:180-214` | `del node.value[index]` for the merge entry, recurse into the source, `merge.extend(...)`, finally `node.value = merge + node.value`. |
| 7 | `BaseConstructor.construct_mapping` `constructor.py:133-145` | Iterates the (now merged) `node.value`, constructing keys/values into the dict. |

**Where exactly the current failure is:** `yaml_pipeline_config_validator.py:43` (`key = self.construct_object(key_node, deep=deep)`) executes on the merge-tagged key node **before** line 56's `super().construct_mapping(...)` can reach `flatten_mapping`. Reproduced verbatim on the repo interpreter:

```text
ConstructorError: could not determine a constructor for the tag 'tag:yaml.org,2002:merge'
```

**The minimal override:** in the `seen` loop, `continue` when `key_node.tag == _MERGE_TAG`, and keep delegating with `super().construct_mapping(node, deep=deep)`.

**Precise call order after the fix** — `construct_object(root)` → `construct_yaml_map(root)` → `_StrictSafeLoader.construct_mapping(root)` → scan → `SafeConstructor.construct_mapping(root)` → `_StrictSafeLoader.flatten_mapping(root)` (NEW override) → `SafeConstructor.flatten_mapping(root)` → `BaseConstructor.construct_mapping(root)`.

**Is `flatten_mapping` still reached?** Yes, through `super()` — so it must **not** be called explicitly in the override (calling it explicitly would double-flatten).

**May `construct_object` be called on a merge-tagged node at all?** **No — never.** It is mechanically callable but *always* raises, because `SafeConstructor` registers no constructor for `tag:yaml.org,2002:merge` and the `None` fallback is `construct_undefined`. The merge key is not a key of the resulting mapping at all; constructing it is meaningless. Any code path that constructs a key node must skip the merge tag first.

> ⚠️ **The skip-only override is NOT sufficient.** `flatten_mapping` mutates `node.value` **in place**, and a merge-source mapping that is *also* constructed as an object is scanned by its own `construct_mapping` **after** a parent expanded it. Measured on this checkout with a skip-only loader:

| Document | `yaml.safe_load` | skip-only strict loader |
|---|---|---|
| `<<: &c` with `<<: [&a {roles: [ds]}, &b {roles: [analyst]}]` (inline, never constructed) | OK | OK (equal) |
| `defaults: &c` + same nested-colliding sources + `<<: *c` | OK | **`ConstructorError: found duplicate key ('roles')`** |
| `h: &c` + same sources + `<<: [*c, *c]` | OK | **`ConstructorError: found duplicate key ('roles')`** |

Mitigation (adopted in the recommendation): snapshot the **pristine** own-key list in the `flatten_mapping` override and scan *that*. Verified: with the snapshot, both documents above become `equal=True` against the oracle, on **74** schema-accepted merge probes with **0** mismatches.

**Blast radius (honest scoping):** an exhaustive probe of schema-accepted merge documents (own-key subsets + merge sources over the 4 keys, 74 documents) shows **0** loader-level mismatches with the skip-only loader — the false positive only bites documents that the schema rejects anyway (an anchor-holder top-level key is always an `extra_forbidden` key). But it changes *which* error is reported for D-07's exact shape, turning the teachable Russian message into `found duplicate key ('roles')`. That is why the snapshot is in scope.

### Q2 — Detecting the merge key correctly

The canonical test is a direct tag comparison against a module-level constant:

```python
_MERGE_TAG = "tag:yaml.org,2002:merge"   # PyYAML exposes no named constant for this tag

if key_node.tag == _MERGE_TAG:
    continue
```

PyYAML's own `SafeConstructor.flatten_mapping` uses the bare literal at `constructor.py:186` and `constructor.py:205`; `yaml.resolver` exports `DEFAULT_MAPPING_TAG`/`DEFAULT_SCALAR_TAG`/`DEFAULT_SEQUENCE_TAG` but **no** merge-tag constant — hence the local constant.

**Verified by experiment** (tags read back from `yaml.compose(...)`; key node is always a `ScalarNode`):

| Source spelling | Resolved key-node tag | Behaviour |
|---|---|---|
| `<<: *base` | `tag:yaml.org,2002:merge` | merges |
| `!!merge <<: *base` | `tag:yaml.org,2002:merge` | merges (skipped by tag — the literal `<<` is irrelevant) |
| `'<<': {...}` (quoted) | `tag:yaml.org,2002:str` | **ordinary key** — result `{'<<': …}`; must **not** be skipped |

Matching the literal string `'<<'` would incorrectly skip a quoted `'<<'` key — exactly what D-02 forbids.

### Q3 — Existing tests that constrain the override

`tests/unit/test_pipeline_config_validator.py` holds exactly **16** test functions (verified by `rg '^def test_'`), and `rg -i merge` on it returns nothing — confirming D-09's claim. Baseline before any change: `pytest tests/unit/test_pipeline_config_validator.py tests/unit/test_http_pipeline_config.py -q` → **29 passed**.

| Test | Line | What it pins | Effect of the fix |
|---|---|---|---|
| `test_duplicate_top_level_key_is_rejected_not_last_wins` | `test_pipeline_config_validator.py:61` | exactly one error; `"duplicate" in message.lower()`; **`line == 2`** | The only test exercised by the duplicate path. Must stay byte-identical: the scan still builds keys with `construct_object` and raises the same `ConstructorError` with the same `problem_mark`/context marks. |
| `test_valid_document_validates_without_raising` | `:153` | the plain 4-key document is accepted | Non-merge path unaffected (projection is only entered when a merge key is present — and even then it costs 0.57 µs). |
| `test_unknown_key_is_rejected_by_extra_forbid` | `:111` | `path == "score_factors"`, `line is None` | D-07 must not touch a non-anchor extra key; verified `_anchor_holder_keys` returns ∅ for this document. |
| `test_deeply_nested_flow_document_is_rejected_not_recursion_error` | `:207` | `message == _TOO_DEEP_MESSAGE` | Unaffected — the `RecursionError` is raised by the scanner before any mapping is constructed. Re-verified after the design: still `Документ YAML имеет слишком глубокую вложенность`. |
| `test_unreadable_control_char_document_is_rejected_not_unmarked_yaml_error` | `:231` | `message == _UNREADABLE_MESSAGE` | Unaffected — raised at read time. Re-verified: `Документ содержит недопустимые символы`. |
| `test_multi_document_stream_is_rejected_with_a_line` | `:98` | one error, non-null line | Unaffected — `Loader=` stays `_StrictSafeLoader`, so `get_single_data`/`get_single_node` semantics are unchanged. |
| `test_error_to_dict_omits_line_when_none_and_includes_when_set` | `:191` | `line` is omitted when `None` | The new merge-bound reject must pass `line=None` (default) so its row is `{"path": "", "message": …}` — same shape as its siblings. |

**The test that pins the reject envelope verbatim is NOT in that file.** It is `test_put_invalid_error_rows_are_verbatim_and_top_level` at **`tests/unit/test_http_pipeline_config.py:285-307`**, and it asserts:

- `response.status_code == 400` and `"detail" not in body`;
- `body["errors"] == expected`, where `expected` is the validator's own `[error.to_dict() …]`;
- `set(row.keys()) <= {"path", "message", "line"}`, `row["path"] == "score_factors"`, **`"line" not in row`**;
- `container.pipeline_config.save_count == 0` (zero writes).

Its document is the non-merge `score_factors: 1.0` document, so `_anchor_holder_keys` returns ∅ and the English `extra_forbidden` message survives verbatim. **This is the D-09 tripwire — preserve it untouched.**

Sibling envelopes to imitate in the new tests (`tests/unit/test_http_pipeline_config.py:310+`): `test_put_deeply_nested_yaml_returns_400_not_500` asserts `body["errors"] == [{"path": "", "message": _TOO_DEEP_MESSAGE}]`; `test_put_control_char_yaml_returns_400_not_500` asserts the analogous `_UNREADABLE_MESSAGE` row. The merge-bound reject must follow the same `{"path": "", "message": …}` row shape.

### Q4 — The `yaml.SafeLoader`-as-oracle test strategy

**Shape:** a module-level fixture corpus of short document strings, driven by **loops** in a new `tests/unit/test_pipeline_config_merge.py`. Hermetic (pure strings — no files, network or DB) and fast (the whole corpus runs in single-digit milliseconds). Use four groups:

```python
# tests/unit/test_pipeline_config_merge.py
import pytest
import yaml

from backend.domain.errors import PipelineConfigValidationError
from backend.infrastructure.yaml_pipeline_config_validator import (
    _MERGE_TOO_BIG_MESSAGE,
    YamlPipelineConfigValidator,
    _StrictSafeLoader,
)

# Group 1 — loader oracle: every document SafeLoader accepts must yield the SAME mapping.
ORACLE_ACCEPTED: list[str] = [...]

@pytest.mark.parametrize("document", ORACLE_ACCEPTED)
def test_strict_loader_matches_safeloader_oracle(document: str) -> None:
    assert yaml.load(document, Loader=_StrictSafeLoader) == yaml.safe_load(document)

# Group 2 — schema accept: docs resolving to exactly the 4 keys
SCHEMA_ACCEPTED: list[str] = [...]

@pytest.mark.parametrize("document", SCHEMA_ACCEPTED)
def test_merge_document_validates(document: str) -> None:
    YamlPipelineConfigValidator().validate(document)   # must not raise

# Group 3 — duplicate rejects (the PIPE-05 proof)
DUPLICATE_REJECTED: list[str] = [...]

@pytest.mark.parametrize("document", DUPLICATE_REJECTED)
def test_explicit_duplicate_still_rejected(document: str) -> None: ...

# Group 4 — the bound
@pytest.mark.parametrize("document", [BOMB_SIDE_KEYS, BOMB_ROOT_ANCHORED])
def test_merge_bomb_rejected_in_bounded_time(document: str) -> None: ...
```

**Do not hand-write one assert per shape** — the corpus is the point: the nested-collision trap (case 5 below) is exactly what hand-written cases miss.

**Oracle corpus (Group 1 + 2), covering D-03 exhaustively:**

| # | Document | Expected | Why it is in the corpus |
|---|---|---|---|
| 1 | plain 4-key document | equals oracle; `validate()` accepts | regression baseline (PIPE-04) |
| 2 | `<<: &base` + the 4 keys as the merge source | equals oracle; resolves to exactly the 4 schema keys; accepts | canonical merge shape (D-01) |
| 3 | `<<: &base {template: podcast}` + explicit own `template: lecture` | equals oracle; `template == "lecture"`; accepts | **D-03 override-wins** (Pitfall 7) |
| 4 | `<<: [&a {roles: [ds]}, &b {roles: [analyst]}]` + own keys | equals oracle; `roles == ["ds"]` | **D-03 first-source-wins** |
| 5 | own `roles: [analyst]` **and** `<<: &b {roles: [ds]}` | equals oracle; `roles == ["analyst"]` | **D-03 own key overrides merged** |
| 6 | nested inline merge (`<<: &c` whose source has its own `<<: &d`) resolving to the 4 keys | equals oracle; accepts | nesting ≥ 2 must not be refused (depth-bound floor) |
| 7 | `defaults: &c` + nested-colliding sources + `<<: *c` | equals oracle (**the in-place-mutation trap**) | the pristine-snapshot justification (Q1) |
| 8 | `h: &c` + colliding sources + `<<: [*c, *c]` | equals oracle | second flavour of the same trap |
| 9 | `'<<': 1` + own keys | equals oracle; literal `'<<'` key preserved | **D-02** — never match the string |
| 10 | `!!merge <<: &b {x: 1}` | equals oracle | explicit merge tag |
| 11 | `<<: &e {}` (empty merge source) | equals oracle | degenerate shape |
| 12 | `<<: [*a, *a]` (same source twice) | equals oracle | idempotent merge |

**Group 3 (must still be rejected, exactly as before):**

| # | Document | Expected |
|---|---|---|
| 13 | `template: podcast` / `template: lecture` | `ConstructorError` with `"duplicate"` in the message, `line == 2` |
| 14 | the same duplicate **plus** a `<<: &b {…}` | `ConstructorError` with `"duplicate"` — **duplicate rejection is not weakened by a merge** (PIPE-05) |

**Group 4 (bound):** the side-key bomb (fan-out 3, nesting 13) and a root-anchored bomb. Expected: exactly one `PipelineConfigError(path="", message=_MERGE_TOO_BIG_MESSAGE)` with no `line`, and a bounded wall time (Q9).

**Two documents deliberately NOT in the corpus** (documented divergences, see Open Questions): a self-referential merge (`a: &a` + `<<: *a`) — `SafeLoader` returns `{'a': {}}`, the guarded loader refuses it as a cycle; and any document whose only divergence is `SafeLoader`'s silent last-wins on explicit duplicates (Groups 1 and 3 must not be merged).

### Q5 — Bound mechanism: pick ONE

**Recommended: the memoised node-graph projection at the head of `_StrictSafeLoader.flatten_mapping`.** It is option (a)'s node walk applied to the loader's *own* composed graph, so it costs **no second parse and no second loader instantiation** — and it is the same hook that captures the pristine own-key list.

`flatten_mapping` is the unique point where a `MappingNode` is guaranteed pristine, and our override runs before `super()`, i.e. before any merge recursion or `merge.extend(...)`. Guarding it to run once per node makes it both correct and O(#nodes).

**Measured cost on legitimate documents** (repo interpreter, projection in isolation, 1000 iterations each):

| Document | Entries / depth | Projection cost |
|---|---|---|
| plain 4-key (no merge) | 4 / 0 | **0.57 µs** |
| `<<: &b` + 3 own keys (legit merge) | 4 / 1 | **1.16 µs** |
| nested merge, depth 2, resolving to 4 keys | 4 / 2 | **1.71 µs** |

For comparison, one `_StrictSafeLoader` instantiation + parse of that document costs **~200 µs** — so the projection is ~0.5 % of the parse it guards. A separate `yaml.compose()` pre-pass would add a whole second instantiation+parse (~200 µs, ~100× the projection) for no benefit.

**Measured effect on the bomb** (fan-out 3 side-key chain, spy installed on `SafeConstructor.flatten_mapping`):

| Nesting depth | Document chars | Unbounded skip-only loader | Guarded loader |
|---|---|---|---|
| 6 | 253 | 1.9 ms | **rejected in 1.6 ms**, base-flatten calls = 22 |
| 8 | 313 | 6.7 ms | rejected in 1.6 ms |
| 10 | 375 | 63.3 ms | rejected in 1.8 ms |
| 12 | 445 | 503 ms | rejected in 2.0 ms |
| 13 | 480 | 1 488 ms | rejected in 2.1 ms |
| 14 | 515 | **4 297 ms** | rejected in 2.2 ms |

**Why the other options were rejected:**

- **(b) counting inside `construct_mapping`/`flatten_mapping` (materialised entries):** the amplification happens *inside* `flatten_mapping` — `self.flatten_mapping(value_node)` then `merge.extend(value_node.value)` (`constructor.py:188-206`). A counter inside that routine observes the expansion only after the recursive call that materialised it, so it cannot satisfy D-04's "reject **before** the expensive work" for the general case; it can only be a post-hoc tripwire. It also entangles measurement with the in-place mutation it is measuring.
- **(c) reject any mapping whose merge sources themselves contain a merge key:** a single crude metric, which D-04 explicitly rules out — and it is *wrong*: nesting is legitimate (corpus case 6) and `SafeLoader` accepts it, so this rule fails the mandated oracle loop. It would also miss a fan-out bomb at depth 1 (`<<: [*a, *a, … ]`).
- **A separate `yaml.compose()` pre-pass for the bound:** pre-flatten and correct, but pays a second full parse + loader instantiation on every save (~200 µs, measured) and duplicates the parse-error surface. The in-loader hook is strictly cheaper and rides the existing `RecursionError`/`yaml.YAMLError` boundary (D-05). `yaml.compose()` is kept only for D-07 (Q8), where it runs on the rare reject path.

**Deterministically testable?** Yes, on two axes: (i) the projection is a pure function of the composed node graph with memoisation, so given a document the outcome is fixed; (ii) the *bound* is unit-testable at the boundary (fan-out 3 depth 5 = 243 entries → accepted; depth 6 = 729 → rejected — both measured). The one non-deterministic axis is how many *shallow* mappings get flattened before the over-budget one is reached (measured 22 base-flatten calls for the side-key bomb, all on mappings of ≤243 entries) — so the regression assertion must be phrased as "rejected + bounded time", not "flatten was never entered" (Q9).

### Q6 — Bound values

Recommended (**Claude's Discretion** per CONTEXT; listed in the Assumptions Log):

```python
MAX_MERGE_DEPTH = 8        # merge nesting levels below a mapping
MAX_MERGE_ENTRIES = 256    # projected flattened (materialised) mapping pairs
```

Both are checked inside the one projection; reject when either is exceeded. Justification from measurements on this checkout (PyYAML 6.0.3 / CPython 3.12.13, fan-out 3 chain):

| Shape | Merge levels | Chars | Projected entries | Unbounded load | Guarded outcome |
|---|---|---|---|---|---|
| legitimate plain 4-key | 0 | 56 | 4 | ~0 ms | accepted |
| legitimate `<<: &b` + own keys | 1 | 69 | 4 | ~0 ms | accepted |
| legitimate nested inline merge (two chained merges) | 2 | ~90 | 4 | ~0 ms | accepted |
| fan-out 3 chain | 5 | 223 | 243 | 1.5 ms | **accepted** (under budget) |
| fan-out 3 chain | 6 | 253 | 729 | 1.9 ms | **rejected by the entries budget** |
| fan-out 3 chain | 12 | 445 | 531 441 | 503 ms | rejected (~2 ms) |
| fan-out 3 chain | 13 | 480 | 1 594 323 | 1 488 ms | rejected (~2 ms) |
| fan-out 3 chain | 14 | 515 | 4 782 969 | **4 297 ms** | rejected (~2 ms) |
| fan-out 1 chain | 7 | 213 | 8 | ~0 ms | **accepted** |
| fan-out 1 chain | 8 | 233 | 9 | ~0 ms | **rejected by the depth bound** |
| fan-out 1 chain | 20 | 505 | 21 | ~0 ms | **rejected by the depth bound** |
| fan-out 2 chain | 8 | 273 | 256 | ~64 ms | **rejected by the depth bound** (entries alone would have admitted it) |

- **Headroom:** a legitimate config needs exactly **4** flattened entries and **one** merge level (two for the nested inline form). `256` is 64× headroom on entries; `8` leaves 5 levels of headroom on depth. Even `<<: [*a, *a]` is 4-8 entries.
- **The entries budget is the DoS stopper** — it is what turns 4.3 s into ~2 ms. The heaviest mapping the budget still admits (243 entries) flattens in about a millisecond.
- **The depth bound is independently necessary.** A fan-out-1 chain grows entries **linearly** (nesting 20 → 21 entries), so the entries budget alone would never reject it; the depth bound caps the merge chain at 8 levels — far below `sys.getrecursionlimit()` (1000 here), which the existing `_TOO_DEEP_MESSAGE` mapping already guards. Conversely the budget catches wide fan-out at shallow depth (fan-out 3, levels 6+). That is D-04's "defence in depth". The two bounds also demonstrably overlap in neither direction: fan-out 2 at 8 levels is admissible on entries (256) but refused on depth — proof that both are load-bearing.
- **Trap to avoid:** rejecting by depth alone at a small number (e.g. 3) would refuse the legitimate nested inline merge; rejecting by entries alone would allow an unbounded fan-out-1 chain.
- **Pin the boundary with a test.** With the recommended code (`result = (entries, 1 + max_source_depth)`, reject when `result[0] > MAX_MERGE_ENTRIES` or `result[1] > MAX_MERGE_DEPTH`), `result[1]` counts *mapping levels involved in the merge chain* — a mapping with no merge is `1`. Measured with exactly that code: fan-out 3 → levels 5 accepted / 6 rejected (entries); fan-out 1 → levels 7 accepted / 8 rejected (depth); fan-out 2 → levels 8 rejected (depth, entries exactly at budget). Freeze these boundaries in the suite — the local-vs-returned off-by-one is exactly the kind of thing that shifts silently during a refactor.

### Q7 — Message plumbing (D-06)

The full chain, with no HTTP-layer change required:

1. `validate()` raises `PipelineConfigValidationError((PipelineConfigError(path="", message=_MERGE_TOO_BIG_MESSAGE),))` — `PipelineConfigValidationError` is a `DomainError` subclass carrying a `tuple[PipelineConfigError, ...]` in `.errors` (`backend/src/backend/domain/errors.py`).
2. `PipelineConfigError` is a frozen dataclass with `path`, `message`, `line: int | None = None`; `to_dict()` **omits `line` when `None`** (`backend/src/backend/domain/pipeline_config.py:26-41`).
3. `save_pipeline_config(repo, validator, *, yaml_text, now=None)` calls `validator.validate(yaml_text)` **before** `repo.save(...)` (`backend/src/backend/application/use_cases/pipeline_config.py`) — so a reject is **zero writes**.
4. The route catches it and serialises:

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

⇒ **New messages require zero HTTP-layer change.** They must be module-level constants in `backend/src/backend/infrastructure/yaml_pipeline_config_validator.py`, beside the existing four (lines 30-33), so copy stays in one place:

```30:33:backend/src/backend/infrastructure/yaml_pipeline_config_validator.py
_OVER_CAP_MESSAGE = "Документ конфига превышает допустимый размер"
_NOT_A_TEXT_OBJECT_MESSAGE = "Ожидается объект с текстовыми ключами"
_TOO_DEEP_MESSAGE = "Документ YAML имеет слишком глубокую вложенность"
_UNREADABLE_MESSAGE = "Документ содержит недопустимые символы"
```

```python
_MERGE_TAG = "tag:yaml.org,2002:merge"
_MERGE_TOO_BIG_MESSAGE = "Документ содержит слияние (merge), превышающее допустимый размер"
_EXTRA_ANCHOR_KEY_MESSAGE = "Лишний ключ «{key}»: якоря нужно объявлять в самом `<<`"
```

`_MERGE_TOO_BIG_MESSAGE` must **not** be `_OVER_CAP_MESSAGE` (D-06): the bomb is ~500 characters, so an over-cap claim would be false. Note the interpolation template keeps the canonical wording from D-07 — «Лишний ключ «defaults»: якоря нужно объявлять в самом `<<`» — with the key name substituted.

**Where to raise it.** Raise a private exception and map it with its own `except` clause inside the existing `try` around the loader (lines 94-121):

```python
class _MergeExpansionTooLarge(Exception):
    """Raised by the projection; mapped at this boundary to a structured reject."""
```

```python
        except _MergeExpansionTooLarge as exc:
            raise PipelineConfigValidationError(
                (PipelineConfigError(path="", message=_MERGE_TOO_BIG_MESSAGE),)
            ) from exc
```

A plain `Exception` propagates cleanly out of `yaml.load` — PyYAML's `load()` has no bare `except` (`yaml/__init__.py:74-82`) — so it is caught by our own clause. This yields exactly the D-06 envelope `{"path": "", "message": …}` with `line` omitted, matching the sibling rows asserted in `test_put_deeply_nested_yaml_returns_400_not_500` / `test_put_control_char_yaml_returns_400_not_500`. **Alternative (rejected):** raise `ConstructorError(..., _MERGE_TOO_BIG_MESSAGE, ...)` — it would be caught by the existing `yaml.MarkedYAMLError` branch, but that branch attaches a `line` from the node mark, so the envelope would differ from the sibling message-only rows.

**D-05 compliance:** the projection runs inside `construct_mapping`/`flatten_mapping`, i.e. inside `yaml.load`, so a `RecursionError` it might raise is still caught by the existing `except RecursionError` → `_TOO_DEEP_MESSAGE`, and any `yaml.YAMLError` by the existing branch. The new pre-pass cannot become a new 500 path.

### Q8 — The D-07 special case (extra top-level anchor-holder key)

**It is a Pydantic `extra_forbidden` error**, so the message must be rewritten in the `ValidationError` mapping inside `validate()` (lines 130-139). Verified error shape on this checkout:

```text
[{'type': 'extra_forbidden',
  'loc': ('defaults',),
  'msg': 'Extra inputs are not permitted',
  'input': {},
  'url': 'https://errors.pydantic.dev/2.13/v/extra_forbidden'}]
```

**Anchor identity exists only at parse time.** After construction the anchors are gone: the merged pairs are copied into the parent and the alias is the *same node object*, so the returned dict cannot answer "is this extra key an anchor holder?". It **is** answerable from the composed node graph.

**Recommendation: a guarded `yaml.compose()` on the reject path only.** Do not touch the happy path, and do not duplicate the 4-key allow-list.

```python
def _anchor_holder_keys(yaml_text: str) -> set[str]:
    """Top-level keys (outside the schema) whose value node is used as a merge source."""
    try:
        root = yaml.compose(yaml_text, Loader=_StrictSafeLoader)
    except (yaml.YAMLError, RecursionError):
        return set()                              # never a new 500 path (D-05)
    if not isinstance(root, MappingNode):
        return set()
    merge_source_ids = set()
    for key_node, value_node in root.value:
        if key_node.tag == _MERGE_TAG:
            sources = value_node.value if isinstance(value_node, SequenceNode) else [value_node]
            merge_source_ids.update(id(source) for source in sources)
    return {
        key_node.value
        for key_node, value_node in root.value
        if key_node.tag != _MERGE_TAG
        and id(value_node) in merge_source_ids
        and isinstance(key_node.value, str)
        and key_node.value not in PipelineConfigModel.model_fields
    }
```

Verified behaviour:

| Document | `_anchor_holder_keys` |
|---|---|
| `defaults: &base {…}` + `<<: *base` (D-07 shape) | `{'defaults'}` |
| `common: &c {…}` + `<<: *c` | `{'common'}` |
| inline `<<: &base {…}` | `∅` |
| `score_factors: 1.0` (non-merge document) | `∅` |

Then rewrite **only** those rows, in the existing comprehension:

```python
anchor_holders = (
    _anchor_holder_keys(yaml_text) if any(e["type"] == "extra_forbidden" for e in exc.errors()) else set()
)
...
message=(
    _EXTRA_ANCHOR_KEY_MESSAGE.format(key=error["loc"][0])
    if error["type"] == "extra_forbidden" and error["loc"] and error["loc"][0] in anchor_holders
    else error["msg"]
),
```

**Tripwire safety:** `test_put_invalid_error_rows_are_verbatim_and_top_level` uses the non-merge `score_factors` document → `anchor_holders == ∅` → the English message survives verbatim. Genuine unknown keys therefore keep their message, exactly as D-07 requires. The allowed-key set is read from `PipelineConfigModel.model_fields`, so there is no second copy of the four keys.

**Keep the schema-derived `path`.** Emit the row with `path=_loc_to_dot_sep(error["loc"])` (so `"defaults"`) and change only the `message`. D-06 fixes the *merge-bound* path to `""`; D-07 does not specify a path, and the loc-derived path is the existing convention for schema errors — flagged in Open Questions as a minor decision the planner should record.

**Alternative (rejected):** a pre-schema check that raises the D-07 message before `model_validate`. Simpler, but it would short-circuit the other schema errors (e.g. `max_chars: 0`) and report only the anchor problem, so a document with two problems would lose one.

### Q9 — Regression-test performance ("rejected AND fast", not flaky)

**Three properties must be asserted, in this order of robustness:**

1. **Exact structured reject** (deterministic, primary): `validate(bomb)` raises `PipelineConfigValidationError` whose `errors == (PipelineConfigError(path="", message=_MERGE_TOO_BIG_MESSAGE),)` — i.e. one row, `path == ""`, `line is None`, and **not** `_OVER_CAP_MESSAGE` (proving the reject is the merge bound, not the size cap; the bomb is 480 chars ≪ 20 000).
2. **Bounded wall time** with a ≥100× margin: the measured guarded cost is **~2 ms**; the unbounded cost at the same size is **~1.5 s** (nesting 13, 480 chars) and **4.3 s** at nesting 14. A ceiling of `0.5 s` (or a generous `2.0 s`) separates them by two-three orders of magnitude. This is the "fails loudly instead of hanging" property.
3. **Optional instrumentation:** a `monkeypatch` spy on `yaml.constructor.SafeConstructor.flatten_mapping` to record how many times the base routine ran. **Measured: 22 calls** for the side-key bomb — all on shallow mappings (≤243 entries), because the projection rejects the first mapping that would exceed the budget (nesting 6, 729 entries). So the honest assertion is *bounded* (`calls <= 64`), **not** `== 0`; an `== 0` claim only holds for a bomb whose merge sits in the document's own root mapping, and it would be a test that encodes the wrong fact.

```python
BOMB = _merge_bomb(fanout=3, nesting=13)          # 480 chars, ≪ MAX_PIPELINE_CONFIG_CHARS
assert len(BOMB) < MAX_PIPELINE_CONFIG_CHARS

def test_merge_bomb_is_rejected_in_bounded_time() -> None:
    start = time.perf_counter()
    errors = _errors(BOMB)                        # pytest.raises around validate()
    elapsed = time.perf_counter() - start

    assert errors == (PipelineConfigError(path="", message=_MERGE_TOO_BIG_MESSAGE),)
    # ~2 ms measured; unbounded would be ~1.5 s here and minutes at larger nesting.
    assert elapsed < 0.5
```

**The pitfall to avoid — a test that hangs rather than fails.** Size the bomb in the *seconds* band, not the minutes band: nesting 13 → 480 chars → ~1.5 s unbounded; 14 → 515 chars → 4.3 s; 16 ≈ 38 s; and the 20 000-char cap permits hundreds of levels, so a "bigger is safer" bomb would wedge CI. Nesting 13 (or 14) is the sweet spot: bounded ≈ 2 ms, regressed ≈ 1.5-4 s — a loud failure, never a hang. Do **not** size it at nesting 6 (1.9 ms unbounded) either: it would pass even with the bound removed, which makes the test vacuous.

**Do not use `pytest-timeout`** — it is not installed (Environment Availability) and adding a dependency is out of scope. On Windows, `signal.alarm`/`SIGALRM` is unavailable, so a `perf_counter` ceiling is the correct tool.

## Recommended Approach

**Single recommended implementation.** All of it lives in `backend/src/backend/infrastructure/yaml_pipeline_config_validator.py`:

1. **Constants** beside the existing ones (after line 33): `_MERGE_TAG = "tag:yaml.org,2002:merge"`, `MAX_MERGE_DEPTH = 8`, `MAX_MERGE_ENTRIES = 256`, `_MERGE_TOO_BIG_MESSAGE` (D-06), `_EXTRA_ANCHOR_KEY_MESSAGE` (D-07), plus a private `class _MergeExpansionTooLarge(Exception)`.
2. **`_project(node, memo, stack) -> tuple[int, int]`** — a module-level helper returning `(entries, depth)` for a `MappingNode`: own (non-merge) entries + the sum over merge sources (either the `MappingNode` value or each `MappingNode` in a `SequenceNode` value), `depth = 1 + max(source depths)`. Memoised by `id(node)` so it is O(#nodes); `stack` guards a self-referential merge. Raise `_MergeExpansionTooLarge` when either bound is exceeded.
3. **`_anchor_holder_keys(yaml_text) -> set[str]`** — the guarded `yaml.compose()` helper (Q8), used only when the schema produced an `extra_forbidden` error.
4. **`_StrictSafeLoader`** gains:
   - `__init__` storage: `self._own_keys: dict[int, list]`, `self._checked: set[int]`, `self._memo: dict[int, tuple[int, int]]`;
   - a **new** `flatten_mapping` override that (once per node) snapshots `self._own_keys[id(node)] = list(node.value)` and runs `_project(...)` when a merge key is present — **before** `return super().flatten_mapping(node)`;
   - an **edit** to `construct_mapping`: `continue` on `key_node.tag == _MERGE_TAG`, and iterate `self._own_keys.get(id(node), node.value)` so a merge-source mapping that a parent already flattened is still scanned against its pristine own keys. The raised `ConstructorError` keeps the identical message and marks (`"while constructing a mapping"`, `node.start_mark`, `f"found duplicate key ({key!r})"`, `key_node.start_mark`) → the reject envelope is byte-identical (D-02/D-09).
5. **`validate()`**: add `except _MergeExpansionTooLarge` → `_MERGE_TOO_BIG_MESSAGE` (`path=""`, `line` omitted) inside the existing `try`; in the `ValidationError` comprehension, translate `extra_forbidden` rows whose `loc[0]` is in `_anchor_holder_keys(yaml_text)`. Nothing else in the file changes; the `Loader=` argument, the class hierarchy, the schema and the HTTP layer are untouched.
6. **Tests (RED first, per `.cursor/rules/tdd.mdc`)**: a new `tests/unit/test_pipeline_config_merge.py` (oracle corpus, accept list, duplicate-reject list, bound test with the time ceiling, D-07 test) and one PUT round-trip in `tests/unit/test_http_pipeline_config.py` (merge document → 200 → GET returns the identical `yaml` text).

**Rejected alternatives (and why):**

| Alternative | Why rejected |
|---|---|
| Skip the merge tag with no pristine-own-key snapshot | False-rejects the D-07 shape when its merge source is nested and colliding (`found duplicate key ('roles')` — measured), violating D-03 and failing the mandated oracle loop. |
| Call `flatten_mapping` before the `seen` loop | Pitfall 7 / D-02: flattened merged pairs look like duplicates, so a valid local-over-merged override is rejected. |
| Count entries inside `construct_mapping`/`flatten_mapping` | Runs *after* the expansion it is meant to prevent (Q5); entangles the counter with the in-place mutation. |
| Reject any merge source that itself contains a merge key | Single crude metric (D-04) and factually wrong: nesting is legitimate and `SafeLoader` accepts it → oracle violation. |
| A separate `yaml.compose()` pre-pass for the bound on the happy path | An extra loader instantiation + full parse per save (~200 µs) for zero benefit; the in-loader hook reuses the existing error boundary. |
| Detect the merge key by the literal string `'<<'` | D-02: a quoted `'<<'` is a `tag:yaml.org,2002:str` key (verified) and must stay an ordinary key. |
| Reuse `_OVER_CAP_MESSAGE` for the merge bound | D-06: the bomb is ~500 chars — the copy would be false. |
| Raise the bound as a `ConstructorError` | Caught by the `MarkedYAMLError` branch, which attaches a `line`; the row stops matching the sibling envelope. |
| Swap in `yaml.safe_load`/`FullLoader`, or drop `Loader=` | Pitfall 9: silently deletes the duplicate-key contract (PIPE-02) or re-opens arbitrary-object construction. |
| Add `pytest-timeout` for the regression test | Not installed; out of scope for a parse-path fix. A `perf_counter` ceiling with a 100× margin is enough. |
| A wall-clock-only regression assertion | Flaky; the exact-reject assertion is primary, the ceiling is the backstop. |

## Validation Architecture

> `workflow.nyquist_validation` is **absent** from `.planning/config.json` (which contains only `workflow._auto_chain_active: false` and `workflow.use_worktrees: false`) → treated as **enabled**. This section is the source for `17-VALIDATION.md`.

### What this phase validates

Three contracts, all server-side and all provable offline:

1. **PIPE-04 acceptance** — a valid `<<` document parses, validates against the un-widened 4-key schema, persists, and reads back byte-identical.
2. **PIPE-05 bound** — a small merge bomb is refused by the structured 400 in bounded time, with the dedicated message and zero writes; and duplicate-key rejection is provably *not* weakened.
3. **Untouched contracts (regression)** — the reject envelope rows, the sibling messages (`_TOO_DEEP_MESSAGE`, `_UNREADABLE_MESSAGE`, `_OVER_CAP_MESSAGE`, `_NOT_A_TEXT_OBJECT_MESSAGE`), the English `extra_forbidden` message for genuine unknown keys, and the 4-key schema surface.

### The oracle / fixture approach (the heart of the validation)

- **Oracle:** `yaml.SafeLoader` (via `yaml.safe_load`) is the reference implementation for merge semantics. For every document the oracle accepts, `_StrictSafeLoader` must return an **equal** mapping. This is a *loop over a fixture corpus*, never one hand-written assert per shape — hand-written cases are how the nested-collision trap (Q1) stays invisible.
- **Fixtures:** module-level tuples of YAML **strings** in `tests/unit/test_pipeline_config_merge.py`, driven by `pytest.mark.parametrize`. Hermetic (no files, no network, no DB, no container), and each document is < 600 chars, so the whole corpus runs in single-digit milliseconds.
- **Four fixture groups:** (1) oracle-accepted documents; (2) schema-accepted documents (resolve to exactly the 4 keys) asserted through `YamlPipelineConfigValidator().validate()`; (3) documents that must still be rejected for explicit duplicates, with and without a `<<`; (4) the adversarial bomb. Full contents in Q4.
- **One HTTP-level round-trip** in `tests/unit/test_http_pipeline_config.py` (the existing `_real_validator_admin_env()` harness): PUT a merge document → 200 → GET returns the identical `yaml` text. This is the "reads back in a later session" criterion. It stays in **pytest**, never Playwright — Pitfall 24 explicitly names "a merge-key/config test written as a browser test" as a warning sign, and the SPA mock path has no validator at all.

### The adversarial bomb case

- **Shape:** fan-out 3, nesting 13 — the chain `a0: &a0 {k0: v0}`, `a1: &a1 {<<: [*a0, *a0, *a0]}`, … `a13: &a13 {<<: [*a12, *a12, *a12]}` plus the 4 valid keys, i.e. **480 chars** (2.4 % of `MAX_PIPELINE_CONFIG_CHARS`). Projected entries at nesting 13: 3^13 = 1 594 323. Unbounded cost measured **1.49 s**; a nesting-14 variant measures **4.30 s**. Pick one and freeze it in the fixture with a `len(BOMB) < MAX_PIPELINE_CONFIG_CHARS` guard so the reject can never be the size cap.
- **Second shape:** a root-anchored bomb (the document's own root mapping carries `<<: *deep`) so the guard is proven to fire even when the merge is the root's first flatten.
- **What it proves deterministically:** (a) exactly one error row `{"path": "", "message": _MERGE_TOO_BIG_MESSAGE}` with no `line`; (b) `message != _OVER_CAP_MESSAGE`; (c) elapsed time under a ceiling two orders of magnitude above the measured 2 ms; (d) zero writes at the HTTP level. The bomb must **fail in ~1.5 s, never hang** if the bound regresses (Q9).

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PIPE-04 | Valid `<<` document is accepted by the loader and yields the oracle mapping | unit (oracle loop) | `\.venv\Scripts\python.exe -m pytest tests/unit/test_pipeline_config_merge.py::test_strict_loader_matches_safeloader_oracle -q` | ❌ Wave 0 |
| PIPE-04 | Valid `<<` document passes schema validation and resolves to the 4 keys | unit | `… ::test_merge_document_validates -q` | ❌ Wave 0 |
| PIPE-04 | Merge document persists and reads back byte-identical | integration (in-process HTTP) | `… pytest tests/unit/test_http_pipeline_config.py -q` | ✅ file exists, +1 test |
| PIPE-04 | Explicit duplicate still rejected with the same envelope (with and without a `<<`) | unit + HTTP | `… ::test_explicit_duplicate_still_rejected -q` | ❌ Wave 0 |
| PIPE-04 | Reject envelope rows verbatim, zero writes (tripwire) | integration (in-process HTTP) | `… pytest tests/unit/test_http_pipeline_config.py::test_put_invalid_error_rows_are_verbatim_and_top_level -q` | ✅ PRESERVE |
| PIPE-05 | Bomb rejected with `_MERGE_TOO_BIG_MESSAGE`, `path=""`, no `line`, bounded time | unit | `… ::test_merge_bomb_is_rejected_in_bounded_time -q` | ❌ Wave 0 |
| PIPE-05 | D-07 anchor-holder key gets the Russian message naming the key | unit | `… ::test_anchor_holder_key_message -q` | ❌ Wave 0 |
| PIPE-05 | Genuine unknown key keeps the English `extra_forbidden` message, `path` preserved | unit | `… pytest tests/unit/test_pipeline_config_validator.py::test_unknown_key_is_rejected_by_extra_forbid -q` | ✅ PRESERVE |
| PIPE-05 | Depth/entry boundaries (5 accepted / 6 rejected at fan-out 3; 8 accepted / 9 rejected on depth) | unit | `… ::test_merge_bound_boundaries -q` | ❌ Wave 0 |

No requirement in this phase is manual-only, and none needs a browser.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest **9.1.1** (repo `.venv`) |
| Config file | `pyproject.toml` — `[tool.pytest.ini_options]`, `testpaths = ["tests/unit"]`, `pythonpath = ["."]` |
| Quick run command | `\.venv\Scripts\python.exe -m pytest tests/unit/test_pipeline_config_validator.py tests/unit/test_pipeline_config_merge.py tests/unit/test_http_pipeline_config.py -q` |
| Full suite command | `\.venv\Scripts\python.exe -m pytest -q` |
| Baseline (before any change) | `29 passed` — 16 in `test_pipeline_config_validator.py` + 13 in `test_http_pipeline_config.py` |

### Sampling Rate

- **Per task commit:** the quick run command above (target: < 15 s; measured baseline 10.5 s for the two existing files).
- **Per wave merge:** full suite `\.venv\Scripts\python.exe -m pytest -q`.
- **Phase gate:** full suite green before `/gsd-verify-work`; plus the tripwire `test_put_invalid_error_rows_are_verbatim_and_top_level` explicitly green.

### Wave 0 Gaps

- [ ] `tests/unit/test_pipeline_config_merge.py` — the four fixture groups + oracle loop (covers PIPE-04, PIPE-05). Write the **failing** version first (TDD gate): it must fail with `could not determine a constructor for the tag 'tag:yaml.org,2002:merge'` before any production edit.
- [ ] A merge round-trip test added to `tests/unit/test_http_pipeline_config.py` (reuse `_real_validator_admin_env()`; no new harness).
- [ ] A private-symbol import decision: the new tests import `_MERGE_TOO_BIG_MESSAGE` and `_StrictSafeLoader` from the adapter. Importing private names is already the established pattern in `test_pipeline_config_validator.py` (it imports `_TOO_DEEP_MESSAGE`, `_UNREADABLE_MESSAGE`), so no new convention is introduced.
- [ ] No framework install needed; no `conftest.py` change needed (the oracle corpus is pure strings, so no fixtures are shared).

## Code Excerpts

The exact current code the fix touches.

**The adapter under change** — `backend/src/backend/infrastructure/yaml_pipeline_config_validator.py`.

Imports and constants (note: `SequenceNode` is **not** imported yet and is required by the projection; `ConstructorError` and `MappingNode` are):

```21:33:backend/src/backend/infrastructure/yaml_pipeline_config_validator.py
from yaml.constructor import ConstructorError
from yaml.nodes import MappingNode

from backend.domain.errors import PipelineConfigValidationError
from backend.domain.pipeline_config import PipelineConfigError

# Server-side cap rejected before parse (T-16-07: YAML alias / oversized document DoS).
MAX_PIPELINE_CONFIG_CHARS = 20000

_OVER_CAP_MESSAGE = "Документ конфига превышает допустимый размер"
_NOT_A_TEXT_OBJECT_MESSAGE = "Ожидается объект с текстовыми ключами"
_TOO_DEEP_MESSAGE = "Документ YAML имеет слишком глубокую вложенность"
_UNREADABLE_MESSAGE = "Документ содержит недопустимые символы"
```

The loader — the bug is line **43** running on the merge-tagged key node *before* line **56** can reach `flatten_mapping`:

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

The fixed 4-key schema (not touched — D-01):

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

The parse stage and the `ValidationError` mapping — `except _MergeExpansionTooLarge` goes inside this `try` (after line 121), and the D-07 translation goes in the comprehension at lines 132-138:

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

**The installed PyYAML that governs the mechanic** (`\.venv\Lib\site-packages\yaml\constructor.py`, 6.0.3). `node.value = merge + node.value` (line **213**) is the in-place mutation that makes the pristine snapshot necessary; `merge.extend(...)` (lines 189/202) is the multiplication that makes the bound necessary:

```180:218:.venv/Lib/site-packages/yaml/constructor.py
    def flatten_mapping(self, node):
        merge = []
        index = 0
        while index < len(node.value):
            key_node, value_node = node.value[index]
            if key_node.tag == 'tag:yaml.org,2002:merge':
                del node.value[index]
                if isinstance(value_node, MappingNode):
                    self.flatten_mapping(value_node)
                    merge.extend(value_node.value)
                elif isinstance(value_node, SequenceNode):
                    submerge = []
                    for subnode in value_node.value:
                        if not isinstance(subnode, MappingNode):
                            raise ConstructorError("while constructing a mapping",
                                    node.start_mark,
                                    "expected a mapping for merging, but found %s"
                                    % subnode.id, subnode.start_mark)
                        self.flatten_mapping(subnode)
                        submerge.append(subnode.value)
                    submerge.reverse()
                    for value in submerge:
                        merge.extend(value)
                else:
                    raise ConstructorError("while constructing a mapping", node.start_mark,
                            "expected a mapping or list of mappings for merging, but found %s"
                            % value_node.id, value_node.start_mark)
            elif key_node.tag == 'tag:yaml.org,2002:value':
                key_node.tag = 'tag:yaml.org,2002:str'
                index += 1
            else:
                index += 1
        if merge:
            node.value = merge + node.value

    def construct_mapping(self, node, deep=False):
        if isinstance(node, MappingNode):
            self.flatten_mapping(node)
        return super().construct_mapping(node, deep=deep)
```

Why `construct_object` on a merge-tagged node always raises — no constructor is registered for the tag, so the `None` fallback fires:

```426:429:.venv/Lib/site-packages/yaml/constructor.py
    def construct_undefined(self, node):
        raise ConstructorError(None, None,
                "could not determine a constructor for the tag %r" % node.tag,
                node.start_mark)
```

```479:480:.venv/Lib/site-packages/yaml/constructor.py
SafeConstructor.add_constructor(None,
        SafeConstructor.construct_undefined)
```

And the base loop that constructs every key (line **139** is what our override must stop running on the merge key):

```132:145:.venv/Lib/site-packages/yaml/constructor.py
    def construct_mapping(self, node, deep=False):
        if not isinstance(node, MappingNode):
            raise ConstructorError(None, None,
                    "expected a mapping node, but found %s" % node.id,
                    node.start_mark)
        mapping = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, collections.abc.Hashable):
                raise ConstructorError("while constructing a mapping", node.start_mark,
                        "found unhashable key", key_node.start_mark)
            value = self.construct_object(value_node, deep=deep)
            mapping[key] = value
        return mapping
```

**The HTTP serializer that consumes the messages** — unchanged:

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

**The D-09 tripwire** — byte-identical rows, `score_factors`, zero writes; must not be touched:

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

**The duplicate-key test the edited scan must keep green** (`errors[0].line == 2` is the mark-sensitive assertion):

```61:72:tests/unit/test_pipeline_config_validator.py
def test_duplicate_top_level_key_is_rejected_not_last_wins() -> None:
    """RED→GREEN: SafeLoader last-wins is replaced by a strict duplicate reject."""
    errors = _errors(
        "template: podcast\ntemplate: lecture\nroles:\n  - ds\nlanguage: ru\nmax_chars: 100\n"
    )

    assert len(errors) == 1
    assert "duplicate" in errors[0].message.lower()
    assert errors[0].line == 2
```

## Common Pitfalls

### Pitfall 1: The in-place mutation false positive (the trap this phase must not fall into)
**What goes wrong:** the skip-only fix parses merge documents correctly *until* a merge-source mapping is also constructed as an object — `SafeConstructor.flatten_mapping` has already expanded that node's `value` list in place (`constructor.py:187-189`, `:213`), so its own `construct_mapping` sees merge-introduced collisions and raises `found duplicate key ('roles')`.
**Why it happens:** anchors are shared node objects; "I already flattened this node for my parent" is invisible at the call site.
**How to avoid:** snapshot the pristine own-key list in a `flatten_mapping` override (before `super()`) and scan that snapshot.
**Warning signs:** `flatten_mapping` called before the `seen` loop; a `<<` document rejected with `found duplicate key` on a key that appears only once per source; the oracle corpus containing no nested/colliding case.

### Pitfall 2: Scanning after `flatten_mapping` (the naive inverse fix)
**What goes wrong:** merged pairs are prepended to `node.value`, so a valid local-over-merged override looks like a duplicate (Pitfall 7).
**Why it happens:** "duplicates are bad" and "merges are inlined" are both true and only interact in the override case.
**How to avoid:** keep the scan on the pre-merge own keys; add an explicit accept fixture (`own key` + `<<` source defining the same key) and an explicit reject fixture (`y: 1` / `y: 2` in one mapping, including when a `<<` is also present).
**Warning signs:** any `flatten_mapping` call above the loop that builds `seen`; a merge suite with no overriding keys.

### Pitfall 3: Detecting the merge key by the literal string `'<<'`
**What goes wrong:** a quoted `'<<'` key (tag `tag:yaml.org,2002:str`) is skipped as if it were a merge, so a genuine duplicate on that key escapes, and the key silently changes meaning.
**How to avoid:** compare `key_node.tag == _MERGE_TAG`; add a quoted-`'<<'` fixture and an explicit `!!merge` fixture.
**Warning signs:** the string `'<<'` (with quotes) appearing anywhere in the adapter's logic.

### Pitfall 4: Skipping the merge key without adding the bound
**What goes wrong:** the fix *creates* the DoS path — `flatten_mapping` becomes reachable and multiplies the node list `k^depth`; measured 503 ms at 445 chars and 4.3 s at 515 chars.
**Why it happens:** the existing defences (char cap, `RecursionError` mapping) both miss it — a merge bomb is neither long nor deep.
**How to avoid:** ship the bound in the same diff as the fix; add the adversarial fixture in Wave 0 so there is no intermediate state (ROADMAP success criterion 4).
**Warning signs:** a merge test suite with only single-level merges; no entries/depth guard in the diff; CI wall-clock growth on the validator module.

### Pitfall 5: Enforcing the budget *inside* the expansion
**What goes wrong:** a counter in `construct_mapping`/`flatten_mapping` observes the multiplication only after the recursive `merge.extend(...)` that performed it, so the work has already been paid.
**How to avoid:** project `(entries, depth)` from the composed node graph with memoisation and reject before `super().flatten_mapping(node)`.

### Pitfall 6: A new pre-pass that becomes a new 500 path
**What goes wrong:** a projection/`yaml.compose()` call outside the existing `try` raises `RecursionError`/`ReaderError` straight out of `validate()`, turning a structured 400 into an unhandled 500 (the WR-02/CR-01 contract from Phase 16 regresses).
**How to avoid:** keep the projection inside the loader (inside `yaml.load`), and wrap the D-07 compose helper in `except (yaml.YAMLError, RecursionError) → set()` (D-05).
**Warning signs:** a bare `yaml.compose(...)` in `validate()` outside a `try`; a new exception type that no `except` clause catches.

### Pitfall 7: A regression test that hangs, or one that is vacuous
**What goes wrong:** sizing the bomb at nesting 16+ (or at the 20 000-char cap) makes a regressed build wedge CI for minutes; sizing it at nesting 5-6 makes a regressed build pass in 2 ms.
**How to avoid:** pick the *seconds* band (nesting 13 → ~1.5 s unbounded, ~2 ms bounded) so a regression fails loudly in ~1.5 s; assert the exact reject row first, then the time ceiling.
**Warning signs:** a bomb fixture whose unbounded cost was never measured; a time assertion with no measured margin; relying on `pytest-timeout` (not installed) or `SIGALRM` (unavailable on win32).

### Pitfall 8: Reusing `_OVER_CAP_MESSAGE` for the merge bound
**What goes wrong:** the bomb is ~500 chars, so «Документ конфига превышает допустимый размер» is factually false and sends the admin hunting a size problem that does not exist.
**How to avoid:** the dedicated D-06 constant, asserted **not equal** to `_OVER_CAP_MESSAGE` in the test.

### Pitfall 9: Translating the wrong "extra key"
**What goes wrong:** replacing the message for every `extra_forbidden` error turns a genuine typo (`score_factors`) into an anchor lecture, and breaks the D-09 tripwire.
**How to avoid:** gate on anchor identity from the composed graph (`_anchor_holder_keys`), which is ∅ for `score_factors`; keep the English message otherwise.

### Pitfall 10: Writing the RED test as a browser test
**What goes wrong:** `VITE_USE_MOCKS=true` means the SPA has no validator at all, so a Playwright test either cannot fail or fails for a mock reason and then gets "fixed" in the mock (Pitfall 24).
**How to avoid:** pytest only. Playwright would be integration proof at most, and none is required here.

## Code Examples

Verified patterns (all snippets confirmed to run against the repo `.venv`; write the failing tests from these first).

### The projection (memoised, cycle-guarded, pre-flatten)

```python
def _project(
    node: MappingNode,
    memo: dict[int, tuple[int, int]],
    stack: set[int],
) -> tuple[int, int]:
    """Return (flattened entries, merge depth) for a mapping node; raise when over budget."""
    node_id = id(node)
    if node_id in memo:
        return memo[node_id]
    if node_id in stack:
        raise _MergeExpansionTooLarge        # self-referential merge
    stack.add(node_id)

    entries = 0
    depth = 0
    for key_node, value_node in node.value:
        if key_node.tag == _MERGE_TAG:
            sources = value_node.value if isinstance(value_node, SequenceNode) else [value_node]
            for source in sources:
                if isinstance(source, MappingNode):
                    source_entries, source_depth = _project(source, memo, stack)
                    entries += source_entries
                    depth = max(depth, source_depth)
        else:
            entries += 1
    stack.discard(node_id)

    result = (entries, 1 + depth)
    if result[0] > MAX_MERGE_ENTRIES or result[1] > MAX_MERGE_DEPTH:
        raise _MergeExpansionTooLarge
    memo[node_id] = result
    return result
```

### The loader: one new hook, one edited loop

```python
class _StrictSafeLoader(yaml.SafeLoader):
    def __init__(self, stream: Any) -> None:
        super().__init__(stream)
        self._own_keys: dict[int, list[Any]] = {}
        self._checked: set[int] = set()
        self._memo: dict[int, tuple[int, int]] = {}

    def flatten_mapping(self, node: MappingNode) -> None:
        if isinstance(node, MappingNode) and id(node) not in self._checked:
            self._checked.add(id(node))
            if any(key_node.tag == _MERGE_TAG for key_node, _ in node.value):
                self._own_keys[id(node)] = list(node.value)   # PRISTINE (pre-mutation)
                _project(node, self._memo, set())             # bound first, expand later
        return super().flatten_mapping(node)

    def construct_mapping(self, node: MappingNode, deep: bool = False) -> dict[Any, Any]:
        if isinstance(node, MappingNode):
            seen: set[Any] = set()
            own_keys = self._own_keys.get(id(node), node.value)
            for key_node, _value_node in own_keys:
                if key_node.tag == _MERGE_TAG:
                    continue                                  # D-02: by tag
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

### The oracle loop (the test that makes the corpus the contract)

```python
@pytest.mark.parametrize("document", ORACLE_ACCEPTED)
def test_strict_loader_matches_safeloader_oracle(document: str) -> None:
    # For every document SafeLoader accepts, the strict loader must not change the mapping.
    assert yaml.load(document, Loader=_StrictSafeLoader) == yaml.safe_load(document)
```

### Anchor-holder detection used only on the reject path

```python
try:
    root = yaml.compose(yaml_text, Loader=_StrictSafeLoader)
except (yaml.YAMLError, RecursionError):
    return set()                                   # D-05: never a new 500 path
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|---|---|---|---|
| Construct every key node, then delegate (the current override) | Skip merge-tagged keys by tag and scan a pristine own-key snapshot | Phase 17 | Valid `<<` documents stop failing with an internal tag name; D-03 override semantics survive nesting. |
| Trust the source-length cap as the DoS defence | Bound the *projected* expansion (entries + depth) before it materialises | Phase 17 | A 480-char document can no longer burn seconds of CPU; ROADMAP criterion 3 becomes provable. |
| Let the parser's internal error text reach the 400 body | Map every parser failure at the adapter boundary to curated Russian copy | Phase 16 (WR-02/CR-01) → extended in Phase 17 | `tag:yaml.org,2002:merge` never appears in a response body; the anchor-holder mistake becomes teachable. |

**Deprecated/outdated (do not use in this phase):**
- `yaml.safe_load` / `yaml.load` without `Loader=` / `FullLoader` — Pitfall 9: removes duplicate-key rejection or re-opens arbitrary-object construction.
- `PITFALLS.md`'s provisional phase numbers ("Phase 19") for this work — the roadmap assigns it **Phase 17**; address pitfalls by name.
- `PITFALLS.md`'s CPython 3.14 timings — this checkout is CPython 3.12.13; use the timings in this document.

## Runtime State Inventory

**Omitted by design.** Phase 17 is a pure parse-path fix inside one adapter — no rename, no migration, no persisted key changes. Nothing to inventory: the raw YAML text is stored verbatim and expanded only at validation time, so previously-saved documents need no migration, and no live service, OS registration, secret name, or build artifact references the merge tag.

## Security Domain

> `security_enforcement` is absent from `.planning/config.json` → **enabled**.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | The PUT route is admin-gated by the existing `require_admin` dependency; unchanged by this phase. |
| V3 Session Management | no | Untouched. |
| V4 Access Control | no | No new surface; the validator is reached only through the existing admin route and the `PipelineConfigValidator` port. |
| V5 Input Validation | **yes** | `yaml.SafeLoader` subclass (strict duplicate keys, text-only top-level keys) + the fixed Pydantic `extra="forbid"` model + the new merge-expansion bound. This phase *strengthens* V5 by turning an accidental fail-closed into a deliberate, bounded accept. |
| V6 Cryptography | no | No secret, hash or cipher in this phase. The 4-key schema deliberately excludes credential keys (PIPE-03) and must not be widened (D-01). |
| V7 Error Handling & Logging | **yes** | Parser internals are mapped to curated copy at the adapter boundary; the 400 body carries no loader internals (the pre-fix leak was `tag:yaml.org,2002:merge`). |
| V11 Business Logic | partial | The bound is a business rule of the parse gate; it must be enforced server-side (it is — no client involvement). |

### Known Threat Patterns for the PyYAML / FastAPI stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Parser amplification (merge fan-out / nesting) → CPU exhaustion | Denial of Service | The `(entries, depth)` projection at the head of `flatten_mapping`, rejected before expansion; plus the 20 000-char cap. |
| Parser recursion overflow (nested flow collections) | Denial of Service | Existing `RecursionError` → `_TOO_DEEP_MESSAGE` mapping (WR-02); the projection's recursion is bounded by `MAX_MERGE_DEPTH`, so it cannot newly overflow. |
| Arbitrary object construction via unsafe tags | Elevation of Privilege / Tampering | `SafeLoader` subclass only; the `None` constructor falls back to `construct_undefined` (fails closed). Never `FullLoader`/`UnsafeLoader`/no-`Loader=` (Pitfall 9). |
| Alias amplification ("billion laughs") | Denial of Service | Assessed as *not* the amplifier here (Pitfall 9: 200 alias levels cost ~15 ms because aliases are shared references); the char cap remains the outer shell. Do not swap loaders to "fix" it. |
| Information disclosure through error text | Information Disclosure | Map every parser failure at the adapter boundary (Pitfall 1's warning sign: the literal `tag:yaml.org,2002:merge` must never appear in a 400 body). |
| Unvalidated input reaching persistence | Tampering | Validate-before-save with zero writes (`save_pipeline_config` calls `validate()` before `repo.save()`); the new rejects preserve this. |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `MAX_MERGE_DEPTH = 8` and `MAX_MERGE_ENTRIES = 256` are the right numbers | Q6 | Claude's Discretion per CONTEXT; too tight refuses a legitimate nested config, too loose re-opens CPU cost. Evidence: 4 entries / depth 1-2 needed; 243 entries accepted, 729 rejected; measured bounded cost ~2 ms. |
| A2 | The D-07 row keeps the schema-derived `path` (`"defaults"`), changing only `message` | Q8 | D-07 specifies no path; if the planner wants `path: ""` for symmetry with D-06, that is a one-line change — but pick one deliberately, since the UI renders `path`. |
| A3 | A self-referential merge (`a: &a` + `<<: *a`) may be refused with `_MERGE_TOO_BIG_MESSAGE` instead of mirroring `SafeLoader`'s `{'a': {}}` | Q4/Q5 | The document is rejected either way (the anchor-holder key is `extra_forbidden`), so no accepted behaviour changes; but the oracle corpus must exclude it and a dedicated test must pin the divergence. |
| A4 | The shipped bomb fixture is fan-out 3 / nesting 13, with a `0.5 s` ceiling | Q9 | A different size/ceiling changes only how fast a regressed build fails; nesting 13 keeps it in the seconds band and the ceiling has a ≥250× margin. |
| A5 | The allowed-key set for anchor detection is read from `PipelineConfigModel.model_fields` | Q8 | Avoids a second copy of the 4 keys; if the schema gains a key later, the D-07 detection follows automatically. |
| A6 | Duplicates **inside** an inline merge-source mapping (`<<: &b` whose block repeats a key) stay merge-introduced collisions (accepted, last-wins in the source) | Q1/D-03 | Reproduced behaviour with the skip-only **and** snapshot loaders. It is covered by D-03's "merge-introduced collisions are not errors", but it should be pinned by an explicit test so it is a decision rather than an accident. |

**If this table is empty:** not applicable — the entries are the phase's open calibration points, all within Claude's Discretion except A2/A3/A6, which the planner should record explicitly.

## Open Questions (RESOLVED)

1. **What `path` should the D-07 row carry — `""` (like D-06) or the offending key name (like every other schema error)?**
   - What we know: the existing `extra_forbidden` row carries `path == "score_factors"` and the UI/tests treat that as the field identity; D-06 fixes the merge-bound path to `""` but D-07 says nothing.
   - Recommendation: keep the loc-derived `path` (`"defaults"`) and change only `message`; that is the smallest change and the most informative row. Record it in the plan.
   - **RESOLVED:** keep the loc-derived `path` (`"defaults"`) and change only `message` — planned in `17-02-PLAN.md` Task 1 (`_anchor_holder_keys` + the anchor-gated translation inside the existing `ValidationError` comprehension) and proved end-to-end by that plan's `test_put_anchor_holder_key_returns_400_with_teaching_message`, which asserts `body["errors"] == [{"path": "defaults", "message": …}]` with no `line`. That keeps the row's field identity identical to every other `extra_forbidden` row (Assumption A2).

2. **Should duplicates inside an inline merge-source mapping be rejected?**
   - What we know: they are currently accepted (last-wins inside the source) with both candidate loaders; D-03 arguably covers them as merge-introduced.
   - Recommendation: keep them accepted and pin the behaviour with an explicit test (Assumption A6), so the strictness boundary is documented rather than incidental.
   - **RESOLVED:** kept accepted, recorded as a deliberate decision (Assumption A6) rather than an accident. `SafeConstructor.flatten_mapping` splices a merge source's entries into the outer mapping node and never constructs the source mapping on its own, so the pre-merge own-key scan fixed by D-02 cannot see a key repeated *inside* one inline source; the repeat therefore resolves last-wins inside that source, matching `yaml.safe_load` (reproduced on this checkout). Duplicate rejection — the PIPE-05 / ROADMAP criterion-2 proof — stays on the explicit own-key list of the mapping being validated: `17-01-PLAN.md` Group 3 pins it with and without a `<<` present, and the Group 1 oracle rows pin loader agreement with `yaml.safe_load` on colliding merge sources (`<<: [*a, *b]`, own key over merged key, `<<: [*c, *c]`). A dedicated accepted-fixture row for a key repeated *inside* one source is deliberately not added: it would read against ROADMAP criterion 2's "duplicated **explicit** key" wording while adding no behaviour claim beyond the oracle rows — and rejecting such a document instead would break the mandated `SafeLoader` oracle contract.

3. **Does the `_validate` order need the bound *before* the schema check?**
   - What we know: it already is — `yaml.load` (line 95) runs before `model_validate` (line 129), so a merge bomb is refused before the schema ever sees the (correctly small) parsed dict.
   - Recommendation: no change; assert it in a test only if it is cheap to do so.
   - **RESOLVED:** no ordering change. The bound fires inside `yaml.load` (parse stage) and `PipelineConfigModel.model_validate` runs on the parsed dict afterwards, so the ordering holds by construction in `17-01-PLAN.md` Task 1. It is asserted cheaply: the bomb fixtures are also schema-invalid (13–14 side keys) yet must fail with `_MERGE_TOO_BIG_MESSAGE` and never with an `extra_forbidden` row — which is only possible if the bound ran first.

4. **Is `MAX_MERGE_ENTRIES = 256` meant to count only the root mapping, or every mapping in the document?**
   - What we know: a side-key bomb puts no merge on the root mapping, so a root-only guard would never fire (measured: the guard must reject a nesting-13 side-key chain, whose root has 18 own keys and no merge).
   - Recommendation: every mapping reached by `flatten_mapping` (the current design), which is what the measurements cover.
   - **RESOLVED:** every mapping reached by `flatten_mapping`, not just the root — implemented as the memoised `_project` projection invoked from the loader's own `flatten_mapping` override (`17-01-PLAN.md` Task 1, per D-04). A root-only guard would never fire on the phase's own bomb fixture, whose root mapping carries no merge at all; the budget therefore counts the projected flattened pairs of the whole merge-connected graph.

5. **Are the bound values (`MAX_MERGE_DEPTH = 8`, `MAX_MERGE_ENTRIES = 256`) and the bounded-time regression tooling settled?**
   - What we know: the numbers are **Claude's Discretion** per `17-CONTEXT.md` and are headroom-chosen from measurements on this checkout (Assumption A1), **not** derived from a specification: a legitimate 4-key document needs 4 entries and 1–2 merge levels, while the entries budget is the measured DoS stopper (nesting 14: 4 297 ms unbounded → ~2 ms guarded). `pytest-timeout` is not installed and `signal.SIGALRM` is unavailable on win32 (Pitfall 7).
   - Recommendation: fix the numbers in the plan as module constants and pin the frozen boundary table with a test; use an in-test wall-clock ceiling instead of a timeout plugin.
   - **RESOLVED:** settled **by disposition, not by derivation**. D-04 locks two independent bounds (defence in depth: depth refuses the linear fan-out-1 chain the entries budget would never catch; entries refuse the wide fan-out that depth alone would only catch late), and `17-01-PLAN.md` ships `MAX_MERGE_DEPTH = 8` / `MAX_MERGE_ENTRIES = 256` as module constants pinned by `test_merge_bound_boundaries` (fan-out 3 → 5 accepted / 6 rejected; fan-out 1 → 7 accepted / 8 rejected; plus the exact-`256`-entry acceptance and `257`-entry refusal). The bounded-time regression uses an in-test `time.perf_counter()` ceiling of 0.5 s (≥250× margin over the ~2 ms guarded cost); `pytest-timeout` is deliberately not added and `SIGALRM` is not used.

## Sources

### Primary (HIGH confidence) — read in this session
- `.venv/Lib/site-packages/yaml/constructor.py` (PyYAML 6.0.3) — `construct_object` 66-116, `BaseConstructor.construct_mapping` 132-145, `SafeConstructor.flatten_mapping` 180-213, `SafeConstructor.construct_mapping` 215-218, `construct_yaml_map` 411-414, `construct_undefined` 426-429, `add_constructor(None, …)` 479-480.
- `.venv/Lib/site-packages/yaml/__init__.py` — `compose` 51-60, `load` 74-82 (no bare `except`, so a custom exception propagates cleanly).
- `backend/src/backend/infrastructure/yaml_pipeline_config_validator.py` — constants 28-33, loader 36-56, schema 59-71, `validate` 88-139.
- `backend/src/backend/interface/http/routes/admin.py` 577-585; `backend/src/backend/domain/pipeline_config.py` 26-41; `backend/src/backend/domain/errors.py`; `backend/src/backend/application/use_cases/pipeline_config.py`.
- `tests/unit/test_pipeline_config_validator.py` (16 tests, all lines verified), `tests/unit/test_http_pipeline_config.py` 285-307 (tripwire) and 310+ (sibling envelopes).
- Runtime probes run this session with `.venv\Scripts\python.exe` — merge-tag reproduction, oracle comparisons over 74 schema-accepted merge documents, the false-positive probes, the bomb timings, the projection cost, and the anchor-holder detection.
- Project docs read: `17-CONTEXT.md`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md` (Phase 17), `.planning/research/PITFALLS.md` § 6/7/8/9/24, `.planning/config.json`.

### Secondary (MEDIUM confidence)
- `.planning/research/PITFALLS.md` § Pitfall 8 — the *shape* of the DoS and the recommended bound class; its **timings are CPython 3.14** and do not match this checkout (its level-12 figure is 838 ms vs 503 ms measured here for a comparable shape).
- `.planning/research/PITFALLS.md` § Pitfall 6/7/9/24 — the bug description, the naive fix, the loader constraint, and the "never a browser test" constraint; all four independently re-verified here.

### Tertiary (LOW confidence)
- None. Every claim in this document is either read from installed source, read from a repo file, or measured on this checkout.

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** — versions read from `.venv`; no package is added.
- Architecture: **HIGH** — the call order and the two hooks were traced through the installed PyYAML source and reproduced by running candidate loaders.
- Pitfalls: **HIGH** — the mutation trap, the bound bypass, the quoted-`'<<'` behaviour and the tag error are all reproduced; the duplicate-strictness boundary is pinned by probes.
- Bound values: **MEDIUM** — the numbers come from measurements and are Claude's Discretion (Assumption A1), not a locked decision.

**Research date:** 2026-10-14
**Valid until:** 2027-01-12 (90 days — PyYAML 6.0.3 is stable and the phase depends on nothing else)
