---
phase: 13-admin-material-email-preview-honesty
plan: 02
subsystem: api
tags: [email-html, interstitial, preview, settings, tdd, adux-02, adux-03, adux-04]

requires:
  - phase: 13-admin-material-email-preview-honesty
    provides: Enriched shortlist DTO (title/dek/slug) from Plan 13-01
provides:
  - "render_interstitial_html / render_material_email_block / render_email_html (stdlib html.escape)"
  - "DigestEmailPreview.html + DigestPreviewResponse.html on POST /admin/shortlist/preview"
  - "Settings.site_url from SITE_URL → PUBLIC_SITE_URL → http://127.0.0.1:5173"
  - "Plain body internal \\n\\n preservation + enriched plain material URL segments"
  - "Assert-only FORBIDDEN_LOWER + contains_forbidden_chrome (no runtime strip)"
affects:
  - 13-04 Email preview iframe (FE consumes html)
  - 13-05 Ban scrub / FIX-01 notes
  - 13-06 Send/mailer HTML parity

actuals:
  tokens: 5684
  tasks: 3
  commits: 5
plan_head_before: d3fba1e90fcaca4097cc65d26d2c02d9f319a70f
plan_head_after: 557aefe33c41a8b36994bb2d7e5599b3dcbd391d

tech-stack:
  added: []
  patterns:
    - "Pure email_render helpers with site_url default for send callers until Plan 06"
    - "Assert-only email_chrome ban list; renderers must not import it (D-17)"
    - "Preview HTML built in use-case; router only passes trusted Settings.site_url"

key-files:
  created:
    - tests/unit/test_email_render.py
    - backend/src/backend/application/use_cases/email_render.py
    - backend/src/backend/domain/email_chrome.py
  modified:
    - tests/unit/test_preview_digest.py
    - backend/src/backend/application/use_cases/preview_digest_email.py
    - backend/src/backend/composition/settings.py
    - backend/src/backend/interface/http/routes/admin.py
    - .env.example

key-decisions:
  - "render_email_html blocks use Mapping kind=material|text so preview can rebuild ordered composition without coupling to PreviewBlock types in the renderer"
  - "site_url defaults on render helpers and compose_digest_segments keep send path green until Plan 06 wires trusted Settings"
  - "Ban list stays assert-only — source guard test locks email_render free of email_chrome imports"

patterns-established:
  - "Interstitial: strip → html.escape → \\n\\n→<p> → \\n→<br>"
  - "Material email block: <h2>title</h2> + optional dek <p> + Читать → absolute /materials/{slug}"
  - "Plain material segment: title + optional dek + absolute reader URL (StubMailer log honesty)"

requirements-completed: [ADUX-02, ADUX-03, ADUX-04]

coverage:
  - id: D1
    description: "Interstitial matrix + material/email HTML renderers with escaped title/dek and Читать link"
    requirement: ADUX-02
    verification:
      - kind: unit
        ref: "tests/unit/test_email_render.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "POST preview returns additive html with interstitial <p> tags; no issue URL in HTML"
    requirement: ADUX-02
    verification:
      - kind: unit
        ref: "tests/unit/test_preview_digest.py#test_preview_html_present_with_interstitial_paragraphs"
        status: pass
    human_judgment: false
  - id: D3
    description: "Plain body preserves internal blank lines; plain materials include dek + absolute URL"
    requirement: ADUX-03
    verification:
      - kind: unit
        ref: "tests/unit/test_preview_digest.py#test_preview_plain_preserves_internal_blank_lines"
        status: pass
      - kind: unit
        ref: "tests/unit/test_preview_digest.py#test_preview_plain_material_includes_dek_and_absolute_url"
        status: pass
    human_judgment: false
  - id: D4
    description: "Closed ban tokens detected case-insensitively; clean render fixture has no chrome; renderers do not strip"
    requirement: ADUX-04
    verification:
      - kind: unit
        ref: "tests/unit/test_email_render.py#test_contains_forbidden_chrome_detects_hyphen_underscore_concat_case_insensitive"
        status: pass
      - kind: unit
        ref: "tests/unit/test_email_render.py#test_email_render_module_does_not_import_or_call_ban_helper"
        status: pass
    human_judgment: false
  - id: D5
    description: "Settings.site_url from SITE_URL / PUBLIC_SITE_URL / default; documented in .env.example"
    requirement: ADUX-02
    verification:
      - kind: unit
        ref: "tests/unit/test_preview_digest.py#test_settings_site_url_from_site_url_then_public_then_default"
        status: pass
    human_judgment: false

duration: 8min
completed: 2026-10-02
status: complete
---

# Phase 13 Plan 02: Shared email HTML + interstitial + preview wire Summary

**Backend-owned `render_email_html` ships with interstitial `<p>`/`<br>` matrix, additive preview `html`, SITE_URL settings, and assert-only ban helpers — send parity deferred to 13-06.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-10-02T19:26:49Z
- **Completed:** 2026-10-02T19:34:00Z
- **Tasks:** 3/3
- **Files modified:** 8

## Accomplishments

- Pure `render_interstitial_html` / `render_material_email_block` / `render_email_html` with default `site_url=http://127.0.0.1:5173`
- `POST /admin/shortlist/preview` returns additive `html` from use-case (not router assembly)
- Plain body keeps internal `\n\n`; plain materials include dek + absolute reader URL
- `FORBIDDEN_LOWER` + `contains_forbidden_chrome` assert-only; renderers never import ban helper

## Task Commits

1. **Task 1 RED: Interstitial + email HTML tests** — `be2419b` (test)
2. **Task 1 GREEN: Implement renderers** — `8d6dd74` (feat)
3. **Task 2 RED: Preview html/plain/SITE_URL tests** — `4be7182` (test)
4. **Task 2 GREEN: Wire preview + settings** — `cc4db3b` (feat)
5. **Task 3: Ban assert-only guard** — `557aefe` (test)

## Files Created/Modified

- `backend/src/backend/application/use_cases/email_render.py` — shared HTML renderers (D-07/D-11/D-13)
- `backend/src/backend/domain/email_chrome.py` — closed ban list assert helper (D-18)
- `tests/unit/test_email_render.py` — interstitial matrix + ban/chrome guards
- `backend/src/backend/application/use_cases/preview_digest_email.py` — `html` DTO + plain honesty + site_url
- `backend/src/backend/interface/http/routes/admin.py` — `DigestPreviewResponse.html` + trusted site_url
- `backend/src/backend/composition/settings.py` — `Settings.site_url`
- `tests/unit/test_preview_digest.py` — preview html/plain/settings proofs
- `.env.example` — document `SITE_URL`

## Decisions Made

- HTML composition blocks as `{"kind": "material"|"text", ...}` maps keep renderer free of preview DTO imports
- Default `site_url` on shared helpers avoids breaking send callers before Plan 06
- Ban detection stays out of render path (D-17); source-level guard test locks that

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Critical] RED stubs required for intentional assertion failure**
- **Found during:** Task 1 (Interstitial + email HTML)
- **Issue:** Import-only RED produced collection ERROR (INVALID_RED under GSD evidence gate)
- **Fix:** Minimal stub modules returning `""`/`False` so pytest collects and fails on assertions; GREEN replaced stubs
- **Files modified:** `email_render.py`, `email_chrome.py`
- **Commit:** `be2419b` (stubs) → `8d6dd74` (implementation)

## TDD Gate Compliance

| Task | RED commit | GREEN commit | Evidence |
|------|------------|--------------|----------|
| 1 Interstitial/email HTML | `be2419b` | `8d6dd74` | RED_EVIDENCE_OK (`13-02-task1-red-evidence.json`) |
| 2 Preview wire + SITE_URL | `4be7182` | `cc4db3b` | RED_EVIDENCE_OK (`13-02-task2-red-evidence.json`) |
| 3 Ban assert-only lock | n/a (characterization; behaviors already green from Task 1) | `557aefe` (test guard only) | `-k "forbidden or chrome or ban or header"` → 4 passed |

## Threat Flags

None — html.escape on untrusted editorial text and trusted Settings.site_url match plan threat mitigations T-13-03 / T-13-04; no new packages.

## Known Stubs

None — renderers and ban helper are fully implemented; send `body_html` intentionally deferred to Plan 06.

## Self-Check: PASSED

- FOUND: `backend/src/backend/application/use_cases/email_render.py`
- FOUND: `backend/src/backend/domain/email_chrome.py`
- FOUND: `tests/unit/test_email_render.py`
- FOUND: commits `be2419b`, `8d6dd74`, `4be7182`, `cc4db3b`, `557aefe`
- VERIFY: `uv run pytest tests/unit/test_email_render.py tests/unit/test_preview_digest.py -x` → 28 passed
