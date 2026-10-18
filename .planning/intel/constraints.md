# Constraints (from SPECs)

## TDD Red–Green–Refactor mandatory
- source: docs/digest-cds/technical_specification.md
- type: protocol
- content: Development must follow Red–Green–Refactor. Write a minimal failing automated test first; no production code without a failing test first. Tests assert behavior, not mock presence. Exceptions only for config/generated/one-off prototypes or explicit agreement.

## Content contract — material is prepared article only
- source: docs/digest-cds/technical_specification.md
- type: schema
- content: Material is only an agent-prepared article from transcribed/imported source text plus clarifying search/analysis. Raw transcript, video link, video file, and audio file are not materials and are not shown as material content. Video/audio may be transient pipeline input only. Knowledge cards and digests come from published articles. First suitable mention of a complex term with an existing article must link internally; links mutual or via related block; provenance may link externally.

## FR coverage US-01…US-31 (68 functional requirements)
- source: docs/digest-cds/technical_specification.md
- type: api-contract
- content: Spec defines FR-1…FR-68 covering login, issue, material, voting, knowledge, razbor, admin shortlist/send, archive, and post-v1 quiz/YAML. Story→FR traceability table in appendix. Optimized duplicate returnUrl scenarios into FR-6.

## NFR performance (v1 targets)
- source: docs/digest-cds/technical_specification.md
- type: nfr
- content: NFR-P1 issue p95 ≤ 1.5s; NFR-P2 material p95 ≤ 2s; NFR-P3 knowledge search p95 ≤ 2s with explicit degrade status; NFR-P4 admin shortlist p95 ≤ 2s; NFR-P5 FoundryModels pipeline async, does not block published content.

## NFR availability SLO
- source: docs/digest-cds/technical_specification.md
- type: nfr
- content: NFR-A1 read paths ≥ 99.5% in SVA work hours (Mon–Fri 09:00–19:00 MSK); NFR-A2 planned maintenance ≤1/week, ≥24h notice; NFR-A3 FoundryModels down → published content/voting remain; new pipeline jobs fail/retry; NFR-A4 mail channel down → admin send error, shortlist selection preserved.

## NFR security and contour isolation
- source: docs/digest-cds/technical_specification.md
- type: nfr
- content: NFR-S1 domains `@sberbank.ru` / `@omega.sbrf.ru` only (ADR-0003); NFR-S2 admin/config HTTP 403 for non-admin; NFR-S3 secrets only in Cloud.ru/env, not in repo; NFR-S4 no public foreign LLM/Whisper (ADR-0002); NFR-S5 no storing/publishing video/audio as material.

## NFR logging and admin audit
- source: docs/digest-cds/technical_specification.md
- type: nfr
- content: NFR-L1 structured audit for Approve/Reject, batch select, preview, send, YAML save; NFR-L2 append-only for admin UI; NFR-L3 security events (login success/fail, domain reject, 403); NFR-L4 ops logs with request-id, minimize PII; NFR-L5 audit retention ≥ 90 days.

## NFR reliability and content policy
- source: docs/digest-cds/technical_specification.md
- type: nfr
- content: NFR-R1 Supabase/PostgreSQL backups on team schedule (ADR-0004 consequence), restore drill ≥ quarterly; NFR-R2 sticky TOC viewport constraint; NFR-R3 client validation does not replace server checks; NFR-CONTENT same as content contract (no media-as-material).

## Tech stack v1
- source: docs/digest-cds/technical_specification.md
- type: protocol
- content: App host Cloud.ru VM (ADR-0002); FoundryModels for ML pipeline (ADR-0002); self-hosted Supabase+pgvector on separate VM Docker Compose via supabase-integration (ADR-0004); email domains ADR-0003; design canon design-frontend/; homework app Vite+React+React Router+Tailwind in web/; UI tests Playwright; public leaderboard post-v1 (ADR-0001). Minimum three React app functions: issue+material, voting, knowledge. Environments: local, staging (recommended), production.

## Contour boundaries
- source: docs/digest-cds/technical_specification.md
- type: protocol
- content: Runtime and secrets in Cloud.ru contour; video/audio external pipeline input only; team owns self-hosted Supabase backups/updates/HA; FoundryModels availability per NFR-A3/P5; provider change requires ML-pipeline adapter.

## Global error UX patterns
- source: docs/digest-cds/error_handling.md
- type: protocol
- content: Field errors inline with --color-danger, aria-invalid, focus first error; empty states = serif H2 + one sentence + one primary CTA in content column; network read failures → top banner + Retry; mutation failures → toast/banner not applied, form kept, Retry with idempotent retry + spinner; 401 → login?returnUrl=; 403 → insufficient rights page with CTA to issue; expired session mid-action like 401 + optional sessionStorage draft; unknown id → 404 editorial empty. Russian copy; domain terms per CONTEXT. No alert-per-click; no full-page red wash.

## HTTP / business error contracts by surface
- source: docs/digest-cds/error_handling.md
- type: api-contract
- content: Login — empty fields 400 no auth call; bad domain reject; bad credentials 401 banner; timeout/5xx no session; blocked account 403. Issue — empty issue 200 empty state; closed voting callout muted; load fail banner; wrong issue number 404. Material — missing 404; transcript/video-only without article not published; draft hidden as 404/403 for non-admin. Voting — no selection no send; closed cycle 409; idempotent re-vote 200; offline vote not applied; cross-device conflict 409. Knowledge — whitespace/overlong validation; 0 results honest empty no ML substitution; search 5xx keep query. Razbor — empty list; announce stub; missing ipynb disabled download; 404 id. Admin — send blocked if 0 selected or draft in selection or preview policy unmet; 403 for non-admin; send failure not marked sent; 409 if already sent/composition changed. Archive — empty archive CTA to issue.

## Error handling security and idempotency notes
- source: docs/digest-cds/error_handling.md
- type: nfr
- content: Login must not reveal whether email exists; drafts appear as not found to non-admin; a11y via aria-describedby and role=alert; retry on vote/send must not create duplicate digests or extra votes beyond cycle rules; transcription/import/search/analysis failures must not publish raw text — stay draft until editorial quality gate.
