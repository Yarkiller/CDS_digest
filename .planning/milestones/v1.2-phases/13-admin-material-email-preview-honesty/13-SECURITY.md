---
phase: "13"
slug: "admin-material-email-preview-honesty"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-10-03"
---

# Phase 13 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Admin JWT → GET /admin/shortlist | Draft/ready body enrichment stays admin-only | Shortlist DTO with body_markdown / counts |
| Repository join → AdminShortlistItemResponse | Undeclared fields must not serialize | Response models with extra=forbid |
| Preview composition → HTML string | Untrusted editorial text enters email HTML | intro / title / dek / interstitial |
| Settings.site_url → absolute material links | Must not accept client-supplied base URL | Trusted env/settings only |
| Shortlist DTO → Markdown render | Admin-trusted markdown still sanitized in browser | body_markdown via rehype-sanitize |
| Backend html → iframe srcDoc | Escaped HTML displayed in SPA | preview.html only |
| Admin SPA → iframe sandbox | Must not grant script/form escape hatches | sandbox="" |
| Send composition → body_html | Same escaped HTML as preview; StubMailer only | shared render_email_html |
| Issue URL wrapper → plain body | Must not leak into HTML | plain send wrapper only |
| Operator → shared VM SQL | One-way intentional data mutation | migration 010 scrub |
| Ban helpers → tests only | Must not become silent render filters | assert-only FORBIDDEN_LOWER |
| Mock window flags → shortlist DTO | Test seam must not alter live fetch | useMocks branch only |
| Preview DTO items/body → SPA | Items/plain body stay internal; UI must not paint a second copy | subject + iframe only |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-13-01 | Information Disclosure | AdminShortlistItemResponse body_markdown | high | mitigate | Depends(require_admin); enrich only on existing admin shortlist; no public materials-by-id admin route | closed |
| T-13-02 | Tampering | AdminShortlistResponse construction | medium | mitigate | ConfigDict(extra="forbid"); additive fields declared explicitly | closed |
| T-13-03 | Tampering | render_email_html / render_interstitial_html | high | mitigate | html.escape on title/dek/interstitial; stdlib only | closed |
| T-13-04 | Spoofing | Settings.site_url link href | medium | mitigate | site_url from trusted settings/env; never from preview request body | closed |
| T-13-05 | Tampering | AdminItemPreview react-markdown | high | mitigate | rehype-sanitize (+ remark-gfm, rehype-slug); no raw HTML inject | closed |
| T-13-06 | Tampering | AdminEmailPreview iframe srcDoc | high | mitigate | sandbox=""; only backend-escaped html; no FE HTML assembly | closed |
| T-13-07 | Information Disclosure | Email preview modal | medium | mitigate | Admin-only route + require_admin; preview gated by admin session | closed |
| T-13-08 | Repudiation | email_render / AdminDigestPage | medium | mitigate | Ban helpers assert-only; no runtime strip (D-17) | closed |
| T-13-09 | Tampering | migration 010 UPDATE materials | high | mitigate | Idempotent scrub; human gate before apply; never DB reset | closed |
| T-13-10 | Tampering | send_digest HTML path | high | mitigate | Reuse render_email_html + html.escape; no second unsanitized builder | closed |
| T-13-11 | Information Disclosure | issue URL in HTML | medium | mitigate | Issue URL in plain send wrapper only; HTML from shared renderer | closed |
| T-13-12 | Spoofing | post_shortlist_send site_url | medium | mitigate | request.app.state.settings.site_url only; never from SendDigestRequest | closed |
| T-13-13 | Tampering | Email preview iframe while splitting dialog shell | high | mitigate | Wrappers moved only; sandbox="" and srcDoc={preview.html} retained | closed |
| T-13-14 | Information Disclosure | __DIGEST_ADMIN_MATERIAL_LONG_BODY__ mock seam | low | accept | Flag read only inside fetchShortlist useMocks branch; live Authorization fetch unchanged | closed |
| T-13-15 | Information Disclosure | Email preview success branch | medium | mitigate | Subject + sandboxed iframe only; no preview.body / items ul | closed |
| T-13-16 | Tampering | email-preview-frame during list removal | high | mitigate | Do not edit sandbox="" or srcDoc while removing items list | closed |
| T-13-SC | Tampering | npm/pip/cargo installs | high | mitigate | No new packages in phase plans; gate N/A retained | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on (high) count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

### L1 evidence (grep-depth)

| Threat ID | Evidence |
|-----------|----------|
| T-13-01 | `admin.py` shortlist/preview/send all use `Depends(require_admin)`; body_markdown on admin DTO only |
| T-13-02 | All admin response models use `ConfigDict(extra="forbid")` |
| T-13-03 | `email_render.py` uses `html.escape` on title/dek/href |
| T-13-04 / T-13-12 | Preview and send routes read `request.app.state.settings.site_url`; `SendDigestRequest` / `DigestPreviewRequest` have no site_url field |
| T-13-05 | `AdminItemPreview` mounts Markdown with `rehypeSanitize` |
| T-13-06 / T-13-13 / T-13-16 | iframe `data-testid="email-preview-frame"` has `sandbox=""` and `srcDoc={emailModal.preview.html}` |
| T-13-07 | Preview POST behind `require_admin` |
| T-13-08 | `forbiddenChrome.js` documents assert-only; synced with `email_chrome.FORBIDDEN_LOWER` |
| T-13-09 | `supabase-integration/migrations/010_phase13_scrub_test_header.sql` idempotent UPDATE |
| T-13-10 | `send_digest.py` imports and calls shared `render_email_html` |
| T-13-11 | Issue URL prefixed into `body_text` only; HTML path has no issue_url argument |
| T-13-14 | `__DIGEST_ADMIN_MATERIAL_LONG_BODY__` only in `adminApi.js` useMocks branch |
| T-13-15 | Email success branch renders subject + iframe only (no body/items list) |
| T-13-SC | Phase summaries report no new packages |

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-13-01 | T-13-14 | Playwright mock flag `__DIGEST_ADMIN_MATERIAL_LONG_BODY__` is read only inside `fetchShortlist`'s useMocks branch (same pattern as empty-body flag). Live Authorization fetch is unchanged. Low severity; test seam only. | plan disposition (13-07-PLAN) | 2026-10-03 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-03 | 17 | 17 | 0 | gsd-secure-phase (L1 short-circuit) |

## Security Audit 2026-10-03

| Metric | Count |
|--------|-------|
| Threats found | 17 |
| Closed | 17 |
| Open | 0 |

State B create from PLAN.md threat models (plans 01–08) + SUMMARY threat flags (none open). `register_authored_at_plan_time: true`, `asvs_level: 1`, `threats_open: 0` → L1 grep-depth sufficient; auditor not spawned.

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-03
