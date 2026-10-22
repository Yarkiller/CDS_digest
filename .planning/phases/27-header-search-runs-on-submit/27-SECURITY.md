---
phase: 27
slug: header-search-runs-on-submit
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: 2026-10-22
---

# Phase 27 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.
> Source: five `<threat_model>` blocks in `27-01…27-05-PLAN.md` (register authored at plan time), `## Threat Flags` in the five SUMMARY files (no new threats).

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| `SearchPill` → `navigate({ state: { submitId } })` | A client-generated opaque token crosses into history state | Opaque one-shot marker (`Date.now()-seq`); non-sensitive |
| history state → `KnowledgePage` effect | The marker is read back and compared | Same marker; must never become a URL, selector or cache key |
| header input → `/knowledge?q=` → page effect | Untrusted user text becomes the URL search parameter | Arbitrary user text, up to 500 code points; potentially attacker-chosen |
| page form → `searchKnowledge` adapter | The single execution boundary the counter instruments | `{ q, role, limit, offset }` |
| page render → DOM | `?q` reaches the field, live region, hint block and row output | Attacker-controllable text rendered as text nodes |
| module-scope cache ↔ render | Previously fetched rows re-enter the DOM by a second path | Material titles/snippets, session-scoped |
| `?q` → history | Replaced entries must not accumulate attacker-chosen URLs | URL contents |
| in-memory cache → storage | The one boundary this phase must **not** cross (no persistence) | None — forbidden |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-27-01 | Tampering | `web/src/services/knowledgeApi.js` | high | mitigate | sha256 pin over LF-normalised bytes (`tests/unit/test_knowledge_api_snapshot.js`, `FROZEN_SHA256 = bce5c54e…`); `git diff` clean. Gate verified this run: pass 1 / fail 0 | closed |
| T-27-02 | Repudiation | `tests/unit/test_knowledge_search_single_call_site.js` | medium | mitigate | Failure asserts name the offending relative path; `files.length > 20` anti-vacuum. Verified this run: pass 3 / fail 0 | closed |
| T-27-03 | Tampering / XSS | `qUrl` → `#kb-search` value, row rendering | high | mitigate | Controlled `value` / text children only. `rg "dangerouslySetInnerHTML\|innerHTML\|document\.write\|document\.title\s*="` over `web/src` → empty | closed |
| T-27-04 | Denial of service (client) | the `[qUrl]` effect | medium | mitigate | `validateKnowledgeQuery` (trim + 500 code points) runs before `runSearch`; overlong path issues 0 requests (`KnowledgePage.jsx:158-163`) | closed |
| T-27-05 | Repudiation | `window.__DIGEST_KNOWLEDGE_SEARCH_COUNT__` | medium | mitigate | `readCount` throws when `typeof window[key] !== "number"` (`tests/knowledge.spec.js:79-84`) — a missing instrument fails loudly instead of reading 0 | closed |
| T-27-06 | Information disclosure | `trackGoal(ANALYTICS_GOALS.search, …)` | low | mitigate | Payload is `{ role: roleValue }` only — the raw query never reaches Metrika (`KnowledgePage.jsx:264`) | closed |
| T-27-07 | Tampering / injection | `submitId` in `location.state` | high | mitigate | Compared with `===` against `consumedSubmitIdRef` and stripped with `state: null`; never a URL segment, query value, CSS selector, `getElementById` argument, cache key or `location.href` (`KnowledgePage.jsx:171-187`, `SearchPill.jsx:45-48`) | closed |
| T-27-08 | Information disclosure / persistence | `searchSnapshots` | high | mitigate | Module-scope `Map` only; no `sessionStorage` / `localStorage` / `indexedDB` / cookie in `KnowledgePage.jsx`; dies with the document (reload → counter 1) | closed |
| T-27-09 | Denial of service (render loop) | X-2 `MutationObserver` harness | low | accept | Harness-only, `tests/knowledge.spec.js`; installed once via the `window.__KB_AFFORDANCE_OBSERVER__` guard, reads two DOM facts per callback, writes only into a plain array — cannot self-trigger. Ships to no user. See AR-27-01 | closed |
| T-27-10 | Elevation of privilege (state forgery) | hand-crafted `history.state.submitId` | low | accept | Worst outcome is one extra client-side search against an already-authorized read endpoint under the same role session; no privilege boundary crossed. See AR-27-02 | closed |
| T-27-11 | Denial of service (client) | overlong `?q` | high | mitigate | Same control as T-27-04; the overlong branch returns before any request body is built and the counter stays 0 | closed |
| T-27-12 | Tampering / XSS | overlong text in field and inline node | high | mitigate | Field is controlled `value`; inline copy is `validation.message`, a fixed literal — never the user's text. No `innerHTML` on this path | closed |
| T-27-13 | Spoofing (UI confusion) | `preSearch` reading state instead of `qUrl` | medium | mitigate | `preSearch = qUrl === '' && error === null` derived synchronously from the URL (`KnowledgePage.jsx:379`); asserted for overlong, zero-hit and in-flight | closed |
| T-27-14 | Information disclosure | live region echoing the query | low | mitigate | `knowledgeResultSummary` renders only `«Ищем…»` / `«Найдено 0 материалов»` / `«Показано N»`; `/RAG/` negative assertion on the node's text | closed |
| T-27-15 | Tampering / XSS | `?q` in field, live region, hint block, row titles | critical | mitigate | Text-node / controlled-`value` rendering only. S11 payloads: `<img src=x onerror=window.__KB_XSS__=1>` → `xss: undefined`, `onerror: 0`, no `<img` in the title, no markup in the live region (`tests/knowledge.spec.js:662-675`); source gate forbids all four sinks | closed |
| T-27-16 | Tampering (history poisoning) | `setSearchParams` / `navigate` | medium | mitigate | **Closed 2026-10-22 in Phase 28.** The non-empty header path replaces (`SearchPill.jsx:45-48`), the chip path leaves the URL untouched, and after FU-27-01 the **empty** submit also replaces (`SearchPill.jsx:36` → `navigate('/knowledge', { replace: true })`). Pinned by `an empty header submit replaces the history entry`: from a settled `?q=RAG`, an empty Enter keeps `history.length` unchanged and Back leaves `/knowledge`. Red first: the pre-fix run measured 2 → 3. AR-27-03 stands as the record of why this was accepted rather than mitigated at audit time | closed |
| T-27-17 | Repudiation / availability | error path replaying a cached failure | medium | mitigate | `forgetSearchSnapshot(roleValue, q)` runs in `catch` before `setError` (`KnowledgePage.jsx:270`); the seed-then-fail case proves eviction of an existing snapshot (counter 1 → 2 → 3) | closed |
| T-27-18 | Information disclosure | error `message` rendered in the panel | low | accept | Message is `KnowledgeApiError`'s fixed copy, never the raw server payload or the user's query; the header stays free of it. See AR-27-04 | closed |
| T-27-SC | Tampering | npm installs | high | mitigate | No package install in this phase — `package.json` / `web/package.json` last changed in `b94cbfd` (CI restore), unrelated to phase 27. Package-legitimacy gate still blocks any that appear | closed |

*Status: open · closed · open — below {block_on} threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

**Counts:** 19 threats total · 19 closed · 0 open · **`threats_open: 0`** (closed-out on 2026-10-22 when FU-27-01 landed the `replace: true` on the empty submit; the register no longer carries an accepted-below-threshold item).

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-27-01 | T-27-09 | The X-2 `MutationObserver` exists only inside the Playwright harness. It is installed once per page behind `window.__KB_AFFORDANCE_OBSERVER__`, samples two DOM facts, and appends to a plain array without mutating the DOM, so it cannot retrigger itself. It ships to no user and is not bundled into the app. | project owner (via /gsd-manager) | 2026-10-22 |
| AR-27-02 | T-27-10 | A forged `history.state.submitId` can at most force one additional client-side `searchKnowledge` call. That call runs under the visitor's own role session against an endpoint they are already authorized to read; no other principal's data is reachable and no server-side state changes. | project owner (via /gsd-manager) | 2026-10-22 |
| AR-27-03 | T-27-16 | The empty-header-submit push leaves a previously executed `?q` reachable via Back. Impact is confined to this visitor's own history: the query was already executed with the same session and role, the search is a read-only GET, and history entries are per-tab. Fixing it is a one-line `replace: true` plus a Playwright test and is tracked as FU-27-01 rather than hidden by the accepted-risk record. | project owner (via /gsd-manager) | 2026-10-22 |
| AR-27-04 | T-27-18 | `ErrorPanel` renders the fixed copy from `KnowledgeApiError` (`«Не удалось выполнить поиск. Проверьте сеть.»`), never a raw server payload and never the user's query, so the panel cannot become an exfiltration channel for reflected server text. | project owner (via /gsd-manager) | 2026-10-22 |

**Follow-ups opened by this audit:**

- **FU-27-01 — RESOLVED 2026-10-22 (Phase 28 rider).** `SearchPill.jsx:36` now calls `navigate('/knowledge', { replace: true })` on the empty submit, so no history entry is stacked. Covered failing-first by `an empty header submit replaces the history entry` in `tests/knowledge.spec.js` (RED: `history.length` 2 → 3; GREEN: unchanged, and Back leaves `/knowledge`). Commit `d77412f`. T-27-16 is closed.

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-22 | 19 | 18 | 1 below threshold | orchestrator L1 grep-depth audit (asvs_level 1) via /gsd-manager → gsd-secure-phase 27 |

**Depth note:** `asvs_level: 1` and `block_on: high`. The register was authored at plan time (five parseable `<threat_model>` blocks), so this run verified that each stated mitigation exists rather than scanning for new threats. No `gsd-security-auditor` subagent was spawned; the single residual item is a medium-severity gap already identified as WR-02 in `27-VERIFICATION.md`.

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-22
