# Phase 14: Draft→ready & justification honesty - Context

**Gathered:** 2026-10-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver ADUX-05 and ADUX-06: admin can promote material `draft` → `ready` in the UI (lightweight status flip that unblocks D-85 send without SQL), and shortlist «Обоснование» stays honest — real stored `score_factors` via existing D-79 rules, or the explicit empty copy (never silent fake labels). No `publish_material` / `published_at` / knowledge indexing. No `score_factors` writers, PIPE config UI, or ingest fill (Phase 16 / v1.3+). CLI `--debug` and live SMTP stay out of scope.

</domain>

<decisions>
## Implementation Decisions

### Draft→ready control placement (ADUX-05 UX)
- **D-01:** Per-row «Сделать ready» control **next to the draft badge** on the shortlist row — visual separation: **state ≠ decision** (Approve/Reject cluster stays separate). — **Reversibility:** reversible.
- **D-02:** **Reject auto-ready on Approve** — approve ≠ ready. Operator must promote explicitly. — **Reversibility:** reversible.
- **D-03:** Optional **batch** control appears only when there are **approved drafts** (D-85 blockers). Pending/rejected drafts do not surface batch. — **Reversibility:** reversible.
- **D-04:** **Confirm only for batch**; per-row is **one-click**. Soft empty-body warn (D-10) is the only per-row interstitial. — **Reversibility:** reversible.
- **D-05:** After promote: **optimistic** badge `draft` → `ready` + **silent refetch** (same UX pattern as Approve/Reject). — **Reversibility:** reversible.

### Lightweight ready semantics (ADUX-05 API / domain)
- **D-06:** Promote is a **lightweight status flip only** — sets `materials.status` to `ready`. **Must not** call `publish_material`, set `published_at`, or trigger knowledge indexing. Purpose: unblock D-85 send gate. Full publish would triple Phase 14 scope. — **Reversibility:** costly — SPA/API clients will treat admin ready as status-only; later “true publish” must be a distinct path.
- **D-07:** API is **material-scoped**: `POST /admin/materials/{id}/ready`. Status lives on `materials`, not `shortlist_items`. Decision ≠ ready. Extensible beyond shortlist. FE already has `material_id` from shortlist enrich. — **Reversibility:** costly — route becomes the admin promote contract.
- **D-08:** Batch: **one** endpoint accepting `material_ids[]` with **partial success** (consistent with decision-batch failure handling). FE uses optimistic UI; does not FE-loop as the API strategy. Exact batch path is Claude’s discretion as long as it stays material-scoped under `/admin/materials/…`. — **Reversibility:** costly — batch response shape becomes FE/test contract.
- **D-09:** **Idempotent:** `draft` → `ready`; already-`ready` → **200 no-op**. **No ready→draft** in Phase 14 (reverse deferred). — **Reversibility:** reversible for adding reverse later; changing no-op→409 would be costly for clients.
- **D-10:** **No API quality gate** — empty/missing body is allowed. UI may soft-warn («продолжить?») when body empty; API always allows. Admin control + honesty (empty is a valid state). — **Reversibility:** reversible.

### Justification honesty bar (ADUX-06)
- **D-11:** **Honest-empty only** this phase. Do **not** implement `score_factors` writers, PIPE config UI, or ingest fill. Demo seed factors already exist; leave them. PIPE-01 / ingest stub → Phase 16 / v1.3+. — **Reversibility:** reversible (fillers can land later without undoing honesty).
- **D-12:** **Scope wall (explicit):** no `score_factors` writers / config UI / ingest fill in Phase 14. — **Reversibility:** reversible as a planning constraint.
- **D-13:** **Silent-fake ban everywhere:** FE never fabricates labels; BE maps only real stored factors via `honest_factor_labels` (D-79 ≥2 rule stays); no backend defaults like «релевантность». — **Reversibility:** costly — honesty is a product contract already shipped in Phase 5.
- **D-14:** ADUX-06 done bar: **regression lock** + **Playwright empty assert** + **unit matrix** for `honest_factor_labels` (0 / 1 / 2+ / whitespace). Populated factor UI stays Phase 5 design; light polish only if empty-copy change forces a shared component touch — **no redesign**. — **Reversibility:** reversible.

### Empty «Обоснование» UX
- **D-15:** Exact empty copy (shortlist row only): **`Обоснование недоступно — скоринг не запускался`**. Preserves old phrase for searchability + adds reason. No 0-vs-&lt;2 sub-case distinction in copy. — **Reversibility:** reversible (copy), but Playwright/mocks lock the exact string this phase.
- **D-16:** Placement: **shortlist row only** (material preview modal does not show factors today). Same **muted** style as current empty copy (content state, not error). — **Reversibility:** reversible.
- **D-17:** Mocks + Playwright assert the **exact** string (Phase 13 honesty-assert pattern). — **Reversibility:** reversible.

### Carried forward (do not re-open)
- Phase 5 **D-85**: Approve allowed on drafts; Send blocked while any approved item is still draft.
- Phase 5 **D-79**: ≥2 readable factor labels or honesty empty via `honest_factor_labels`.
- Phase 12/13 shortlist enrich + `extra="forbid"` — additive fields only via explicit model updates.
- Phase 13 preview honesty complete; draft→ready + justification were deferred here.

### Claude's Discretion
- Exact batch route path under `/admin/materials/…` (e.g. collection POST vs nested) as long as D-07/D-08 hold.
- Soft-warn dialog microcopy for empty body («продолжить?»).
- Button label micro-variants («Сделать ready» / RU equivalent) as long as placement (D-01) holds.
- Whether batch confirm copy lists titles or counts.
- Partial-success response field names mirroring existing decision-batch patterns.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & roadmap
- `.planning/ROADMAP.md` — Phase 14 goal, success criteria, ADUX-05 / ADUX-06
- `.planning/REQUIREMENTS.md` — ADUX-05, ADUX-06 wording
- `.planning/PROJECT.md` — v1.2 focus; draft→ready + score_factors honesty cluster
- `.planning/STATE.md` — current position Phase 14

### Prior phase locks
- `.planning/milestones/v1-phases/05-admin-digest-publish/05-CONTEXT.md` — D-79 (factor honesty), D-85 (draft blocks send)
- `.planning/milestones/v1.1-phases/10-cli-composition-uat/10-UAT.md` — UAT #5 (SQL ready workaround), #6 (empty Обоснование)
- `.planning/phases/12-admin-shortlist-empty-batch-contract/12-CONTEXT.md` — shortlist HTTP shapes; deferred draft→ready to Phase 14
- `.planning/phases/12-admin-shortlist-empty-batch-contract/12-FIX-01-LOCK.md` — shortlist DTO contract (`extra="forbid"`)
- `.planning/phases/13-admin-material-email-preview-honesty/13-CONTEXT.md` — preview honesty; deferred ADUX-05/06 here

### Implementation surfaces
- `web/src/pages/AdminDigestPage.jsx` — shortlist rows, draft badge, factor empty copy, approved-drafts send hint
- `web/src/services/adminApi.js` — admin shortlist/decision/preview/send; add mark-ready client
- `backend/src/backend/interface/http/routes/admin.py` — admin routes (`extra="forbid"` DTOs); add materials ready routes
- `backend/src/backend/domain/material.py` — `MaterialStatus`, `as_ready` / `assert_publishable` (**do not** reuse full publish path for ADUX-05)
- `backend/src/backend/application/use_cases/publish_material.py` — **out of path** for this phase (contrast only)
- `backend/src/backend/application/ports/material_repository.py` — `save` / `get` for status flip
- `backend/src/backend/domain/shortlist.py` — `honest_factor_labels` (D-79)
- `backend/src/backend/application/use_cases/get_admin_shortlist.py` — factor_labels assembly
- `backend/src/backend/application/use_cases/send_digest.py` — `DraftInSendPoolError` / D-85
- `backend/src/backend/tests_support/in_memory.py` — in-memory materials/shortlist fakes
- `tests/unit/test_score_factors.py` — extend honesty matrix
- `tests/unit/test_http_admin.py` — admin HTTP unit patterns
- `tests/admin.spec.js` — admin Playwright

### Architecture / TDD
- `.cursor/rules/architecture.mdc` — Ports & Adapters; thin HTTP; FE via `web/src/services/`
- `.cursor/rules/tdd.mdc` / `AGENTS.md` — no production code without failing test first

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `AdminDigestPage.jsx` draft badge + `factorLabelsCaption` (today returns `обоснование недоступно`) — extend in place for promote control + new empty copy.
- `setDecision` / optimistic decision UX in admin FE — mirror for ready flip + silent refetch.
- `MaterialRepository.get` / `save` + in-memory fakes — enough for status-only flip without `publish_material`.
- `honest_factor_labels` + `tests/unit/test_score_factors.py` — extend matrix; do not invent labels.
- Demo seed `score_factors` (migration 005 era) — leave populated demo rows alone.

### Established Patterns
- Admin HTTP: Pydantic `extra="forbid"`; additive routes/DTOs need explicit models + tests.
- Decision mutations: shortlist-scoped POST; **ready is material-scoped** (new pattern by design — status on `materials`).
- Honesty empties (D-79 / Phase 13): never invent content; exact Playwright string asserts.
- Partial success for multi-id admin actions (decision batch) — reuse for ready batch.

### Integration Points
- `POST /admin/materials/{id}/ready` (+ batch) → use-case status flip → `MaterialRepository.save` → shortlist GET reflects `material_status=ready` → D-85 send unblocks.
- Empty `factor_labels` → exact RU copy on shortlist row only.
- Send path unchanged except materials can leave draft via UI instead of SQL.

</code_context>

<specifics>
## Specific Ideas

- Empty copy (exact): `Обоснование недоступно — скоринг не запускался`
- Soft empty-body warn micro-intent: «продолжить?» before per-row flip when body empty
- Batch confirm only; aimed at approved-draft D-85 blockers
- Unit matrix cases called out: `honest_factor_labels` with 0 / 1 / 2+ / whitespace labels
- User framing: Area 2 (lightweight vs full publish) is the scope-deciding choice — keep Phase 14 thin

</specifics>

<deferred>
## Deferred Ideas

- Auto-ready on Approve — rejected for this product
- Full `publish_material` / `published_at` / knowledge indexing on promote
- ready→draft reverse control — Phase 15+
- PIPE-01 config UI / ingest `score_factors` writers — Phase 16 / v1.3+
- Factors display in material preview modal — not shown today; out of Phase 14
- CLI `--debug` — Phase 15
- Live SMTP — v1.3
- Phase 13 backlog reader `/materials/<slug>` errors and cursor-pointer polish — stay in Phase 999.* backlog, not this phase

</deferred>

---

*Phase: 14-Draft→ready & justification honesty*
*Context gathered: 2026-10-03*
