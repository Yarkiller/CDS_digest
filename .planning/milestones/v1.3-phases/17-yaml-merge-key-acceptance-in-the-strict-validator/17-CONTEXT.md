# Phase 17: YAML merge-key acceptance in the strict validator - Context

**Gathered:** 2026-10-14
**Status:** Ready for planning

<domain>
## Phase Boundary

The admin can save a pipeline config that uses YAML merge keys (`<<`) at the top level. The strict
validator accepts it, the config persists, and it reads back in a later session. Merge expansion is
bounded so a tiny document cannot exhaust CPU, and duplicate-key rejection is provably not weakened.

This phase is a **pure parse-path fix inside one adapter**. It does not widen the config schema, does
not touch the editor UI, and does not add any execution/scheduler surface.

**In scope:**
- `_StrictSafeLoader.construct_mapping` in `backend/src/backend/infrastructure/yaml_pipeline_config_validator.py`
- A merge-expansion bound enforced before the expensive flatten step
- Two new Russian error messages inside the existing structured-400 envelope
- RED tests in `tests/unit/` (pytest) — never a browser test

**Out of scope:**
- Any change to the locked 4-key schema `{template, roles, language, max_chars}` (`extra="forbid"`)
- Real anchor **reuse** (`defaults: &base` + `<<: *base`) — deliberately still rejected; see D-01
- Any editor hint / UI copy / UI-SPEC change — deferred (see Deferred Ideas)
- Any execution, scheduler, run/trigger control

</domain>

<decisions>
## Implementation Decisions

### Merge idiom and duplicate-key strictness
- **D-01:** The fix is confined to the parse path; the locked 4-key `extra="forbid"` schema is **not**
  widened. A merge document is accepted only when the merge resolves to exactly those four keys
  (verified shapes: `<<: &base` + 4 keys, and `<<: &base` + an explicit local override). The natural
  anchor-holder style (`defaults: &base` + `<<: *base`) stays rejected — but now with an honest,
  teachable error instead of a cryptic one. — **Reversibility:** one-way — widening the schema later
  changes which documents are accepted, i.e. a published behaviour contract (PIPE-02's validate-before-save
  envelope plus the v1.2 decisions D-01/D-02/D-06 that fixed the four-key set), not a local edit.
  User's rationale, recorded verbatim: *"Только фикс парсинга, схема нетронута"*.
- **D-02:** Duplicate detection stays on the **pre-merge own-key list**; the merge key node is skipped by
  its tag `tag:yaml.org,2002:merge`, **never** by matching the literal string `'<<'` (a quoted `'<<'` is
  an ordinary key). Explicit duplicate keys keep producing the same verbatim top-level structured 400
  `{errors:[…]}` with zero writes. — **Reversibility:** costly — the scan order is PIPE-02's contract and
  is pinned by `test_put_invalid_error_rows_are_verbatim_and_top_level`; `flatten_mapping` must never
  move above the `seen` loop (Pitfall 7).
- **D-03:** Collisions introduced **by** merge follow the YAML spec and are **not** errors: the first
  merge source wins, and an explicit own key overrides a merged key. Only explicit own-key duplicates
  are rejected, so `<<: *base` plus a local overriding key is a legitimate document and must load with
  the local value winning. User's rationale: *"Строгость к явным дубликатам неизменна"* — merge-introduced
  collisions are override semantics, not mistakes.

### Denial-of-service bound
- **D-04:** Two independent bounds, **both enforced before the expensive flatten step**: (a) merge
  depth / fan-out, and (b) a total budget of materialised (flattened) entries. Defence in depth, so no
  legitimate document is refused by a single crude metric. — **Reversibility:** costly — the bound is
  the only thing standing between the fix and a newly reachable DoS; loosening it later re-opens the CPU
  path. Measured evidence on this checkout: **457 chars → 5.26 s**, cost ≈ **×3 per extra level**
  (levels 12/13/14 → 0.70 s / 1.87 s / 5.26 s), i.e. ~15 s at level 15 and ~45 s at level 16 — all far
  inside the 20 000-char source cap. User's rationale: *"И глубина/fan-out слияний, и общий бюджет
  развёрнутых пар — и отказ ДО тяжёлой работы"*.
- **D-05:** Any new pre-pass (`yaml.compose` / node walk) is wrapped in the **same**
  `RecursionError` + `yaml.YAMLError` mapping the loader already has, so a new pre-pass cannot become a
  new 500 path (WR-02 / CR-01 contract from Phase 16).

### Error copy
- **D-06:** A **new dedicated** Russian message for the merge bound: «Документ содержит слияние (merge),
  превышающее допустимый размер». It must **not** reuse `_OVER_CAP_MESSAGE` («Документ конфига превышает
  допустимый размер»), because a merge-bomb document is ~500 characters — claiming it exceeds the size
  cap would be false. Same envelope as its siblings: top-level `{errors:[{path:"", message}]}`, zero
  writes. User's rationale: *"документ ~500 символов, говорить «превышает размер» было бы ложью"*.
- **D-07:** An extra top-level anchor-holder key gets its own Russian message that **teaches the correct
  form**, naming the offending key — canonical wording: «Лишний ключ «defaults»: якоря нужно объявлять в
  самом `<<`» (the key name is interpolated from the document). Rationale: under D-01 this is *the most
  likely* admin mistake after the fix (anyone wanting reuse writes `defaults:`/`common:`/`base:`), and
  leaving it as Pydantic's English «Extra inputs are not permitted» would reintroduce exactly the cryptic
  error this phase exists to remove. User's rationale: *"иначе самый частый сценарий остаётся криптовым"*.

### Editor surface
- **D-08:** No editor hint in this phase. A hint advertising `<<` support would be dishonest while
  anchor reuse does not work (D-01). Recorded as a backlog item instead of scope. User's rationale:
  *"минимальный скоуп и никакой лживой подсказки, пока переиспользование не работает"*.

### Tripwire disposition
- **D-09:** `test_put_invalid_error_rows_are_verbatim_and_top_level` → **PRESERVE**. The reject
  envelope must be byte-identical after the fix. No test currently asserts merge behaviour, so no
  existing merge test needs amending (confirmed by grep on `tests/unit/test_pipeline_config_validator.py`).

### Claude's Discretion
- The numeric values of both bounds (depth/fan-out limit and flattened-entry budget), as long as a
  legitimate 4-key config is never refused and the measured bomb shape is refused fast.
- Pre-pass mechanics: `yaml.compose` + node walk vs. a counting `construct_mapping` — whichever keeps
  the cost out of the flatten step.
- Where the new constants and message strings live (alongside `MAX_PIPELINE_CONFIG_CHARS` and the
  existing `_*_MESSAGE` constants is the natural home).
- Test organisation: new module vs. additions to `tests/unit/test_pipeline_config_validator.py`; the
  `yaml.SafeLoader` oracle loop is required either way.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase definition and requirements
- `.planning/ROADMAP.md` § Phase 17 — goal, requirements `PIPE-04`/`PIPE-05`, success criteria, tripwire disposition, dependency ("Nothing")
- `.planning/REQUIREMENTS.md` — `PIPE-04` (accept valid merge doc while still rejecting duplicate **explicit** keys) and `PIPE-05` (merge expansion bounded, duplicate-key rejection provably not weakened); also `PIPE-02` (the reject envelope that must survive verbatim) and `PIPE-03` (module boundary)
- `.planning/PROJECT.md` — v1.3 milestone framing and why backlog debt runs first
- `.planning/STATE.md` — current focus

### Research evidence for THIS phase (Pitfalls 6–9, 24)
- `.planning/research/PITFALLS.md` § Pitfall 6 — *"Detecting duplicate keys before `flatten_mapping` — the merge tag has no constructor"*: the exact bug, why it happens, and the warning sign "the literal string `tag:yaml.org,2002:merge` appearing in any 400 response body"
- `.planning/research/PITFALLS.md` § Pitfall 7 — *"The naive fix — scanning after `flatten_mapping` — rejects valid documents"*: local-over-merged override must keep loading
- `.planning/research/PITFALLS.md` § Pitfall 8 — *"The correct merge fix silently opens a merge-expansion DoS under the existing char cap"*: the measured cost table and the recommended bound (pre-count with `yaml.compose`, reject nested merges, cap flattened entries) — **this is D-04's source**
- `.planning/research/PITFALLS.md` § Pitfall 9 — alias chains are *not* the amplifier (200 levels / 15 ms); never swap `_StrictSafeLoader` for `yaml.safe_load` or `FullLoader`
- `.planning/research/PITFALLS.md` § Pitfall 24 — *"Mock/live divergence makes the fix invisible to — or unprovable by — the offline Playwright suite"*: explicitly names "a merge-key/config test written as a browser test" as a warning sign. This phase's RED tests are pytest.
- `.planning/research/PITFALLS.md` § Technical Debt Patterns + § Performance Traps — "Scan duplicate keys after `flatten_mapping`" = Never; "Skip merge keys **without** adding a merge-expansion bound" = Never
- `.planning/research/STACK.md` — PyYAML `SafeLoader` subclass fix notes (PyYAML 6.0.3 / Python 3.14 on this checkout)
- `.planning/milestones/v1.2-MILESTONE-AUDIT.md` — `WR-01`, the origin of this debt item (backlog 999.7, formerly Phase 16 code-review advisory)

> **Numbering warning:** `PITFALLS.md` carries a *provisional* phase mapping that predates the shipped
> roadmap — it labels this work "Phase 19". The roadmap assigns 999.7 to **Phase 17**. Address pitfalls
> by name, not by the numbers in that table.

### Code to change / reuse
- `backend/src/backend/infrastructure/yaml_pipeline_config_validator.py` — the ONLY module that parses YAML; holds `_StrictSafeLoader`, `MAX_PIPELINE_CONFIG_CHARS = 20000`, and the `_OVER_CAP_MESSAGE` / `_NOT_A_TEXT_OBJECT_MESSAGE` / `_TOO_DEEP_MESSAGE` / `_UNREADABLE_MESSAGE` constants the new messages must sit beside
- `backend/src/backend/domain/errors.py` — `PipelineConfigValidationError` (carries `PipelineConfigError` entries)
- `backend/src/backend/domain/pipeline_config.py` — `PipelineConfigError(path, line?, message)`
- `backend/src/backend/application/ports/pipeline_config.py` — the `PipelineConfigValidator` port this adapter implements
- `tests/unit/test_pipeline_config_validator.py` — existing validator suite (16 tests, incl. `test_duplicate_top_level_key_is_rejected_not_last_wins`, `test_deeply_nested_flow_document_is_rejected_not_recursion_error`, `test_over_cap_document_is_rejected_before_parse`)

### Rules that constrain the change
- `.cursor/rules/tdd.mdc` — RED-first is mandatory: a failing pytest test must exist before production code
- `.cursor/rules/architecture.mdc` — `yaml`/`pydantic` must stay in `infrastructure/`; they must not reach `domain/` or `application/use_cases/`
- `AGENTS.md` — TDD cycle and the `NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST` rule

No ADR governs YAML merge keys; `docs/adr/0001`–`0004` are unrelated to this phase.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_StrictSafeLoader` (a `yaml.SafeLoader` subclass) — the merge fix is an edit to its
  `construct_mapping` override, not a new loader. Pitfall 9 forbids changing the `Loader=` argument or
  the class hierarchy.
- The four existing `_*_MESSAGE` module constants — the pattern the two new Russian strings follow, so
  copy stays in one place and the structured-400 envelope is uniform.
- `PipelineConfigValidationError` + `PipelineConfigError(path, line?, message)` — the reject value type;
  the bound's breach is raised through the same type with `path=""`.
- The `RecursionError` → `_TOO_DEEP_MESSAGE` and `yaml.YAMLError` → `_UNREADABLE_MESSAGE` mapping
  already in `validate()` — the template for wrapping the new pre-pass (D-05).

### Established Patterns
- **Validate-before-save with zero writes** (PIPE-02): the adapter raises; the HTTP layer maps it to a
  400 `{errors:[…]}`. This phase adds reject reasons, never a new response shape.
- **Cheapest-check-first ordering** in `validate()`: char cap → parse → text-object check → schema. The
  merge bound belongs in the parse stage, before flattening.
- **Adapter-boundary error mapping**: SDK/parser exceptions are translated to domain errors exactly at
  this boundary and never leak upward (WR-02/CR-01).

### Integration Points
- `YamlPipelineConfigValidator.validate()` is called through the `PipelineConfigValidator` port; wiring
  lives in `composition/`. **This phase must not touch composition or the HTTP layer** — the diff is the
  adapter plus its unit tests.
- The HTTP route's existing `{errors:[…]}` serializer is the consumer of the new messages; it needs no
  change, which is itself a success criterion for the PR.

</code_context>

<specifics>
## Specific Ideas

- Verified by reproduction on this checkout, before any change:
  `plain` → ACCEPTED · `<<: &base` (merge-only) → REJECTED with `could not determine a constructor for the tag 'tag:yaml.org,2002:merge'` · `defaults: &base` + `<<: *base` → same REJECTED (plus a schema-level `defaults` problem) · duplicate `template:` → REJECTED with `found duplicate key ('template')`.
- The accepted merge shapes were verified to resolve to exactly `['language', 'max_chars', 'roles', 'template']`:
  `<<: &base` + 4 keys, and `<<: &base` + an explicit overriding `template: podcast`.
- `yaml.SafeLoader` is to be used as the **oracle**: for every document `SafeLoader` accepts, the strict
  loader must produce the same mapping — loop this rather than hand-writing cases (Pitfall 6).
- The regression test for the bomb must assert **both** the structured reject *and* complete fast, so a
  future regression fails loudly instead of hanging CI (Pitfall 8).
- Warning sign to grep for in review: the literal string `tag:yaml.org,2002:merge` must not appear in any
  400 response body.

</specifics>

<deferred>
## Deferred Ideas

- **Editor hint about `<<` support** — a hint next to the raw YAML editor saying merge keys are
  supported. Deferred because it would advertise a capability that anchor reuse (D-01) does not actually
  deliver; it becomes honest only if the schema is ever widened. **Candidate backlog item** for
  `/gsd-review-backlog`; would need a UI-SPEC touch (`16-UI-SPEC.md` A-1 editor section) plus a
  Playwright RED test if ever picked up.

</deferred>

---

*Phase: 17-yaml-merge-key-acceptance-in-the-strict-validator*
*Context gathered: 2026-10-14*
