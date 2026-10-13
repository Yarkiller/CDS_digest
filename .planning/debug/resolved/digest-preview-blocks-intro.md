---
status: resolved
resolved:
  at: 2026-10-13
  evidence: "Intro and ordered blocks reach preview.body end-to-end; G-05-1 closed in v1 Phase 5"
trigger: "G-05-1 — Admin digest letter preview omits intro text; issue blocks should show selected topics as reorderable blocks; optional editor text blocks insertable between articles"
created: 2026-09-21T17:46:00Z
updated: 2026-09-21T17:52:00Z
symptoms_prefilled: true
goal: find_root_cause_only
audit_acknowledged:
  milestone: v1
  at: 2026-09-22
  status: diagnosed
---

## Current Focus

hypothesis: "Phase-5 SPA ships digest editors as dead local state and renders email preview from approved∩ready titles only; intro/schema never reach preview. Reorderable topic blocks and insertable inter-article text-block UI were never implemented (prototype was a line-schema textarea wired into preview; SPA copied labels only)."
bug_class: Bohrbug
known_pattern_candidate: none (no knowledge-base.md)
test: "Read AdminDigestPage + preview_digest_email + adminApi.previewEmail + prototype app.js + UI-SPEC/05-REVIEW IN-01"
expecting: "contextText unused in openEmailPreview; modal ignores body; schema is textarea not blocks; REVIEW already flagged dead UI"
next_action: "Return ROOT CAUSE FOUND (diagnose-only)"

reasoning_checkpoint:
  hypothesis: "G-05-1 has three strands: (1) intro omit = bug vs UI-SPEC feed-preview contract because contextText never wired; (2) reorderable topic blocks = never built; (3) optional connecting text = prototype line-schema intended but SPA never wired, and block-insert UX never built."
  confirming_evidence:

    - "AdminDigestPage openEmailPreview calls previewEmail() with no context/schema; modal maps only subject + items"
    - "05-UI-SPEC Digest editors must feed email preview; 05-04-PLAN assumes feed preview composition locally; 05-REVIEW IN-01 documents dead UI"
    - "design-frontend app.js renderEmailPreview writes context + schema lines with {{articles}}; SPA has no equivalent"
  falsification_test: "If preview modal rendered contextText or API accepted intro and UI showed it, complaint 1 would be false; if schema panel listed approved topics as draggable cards, complaint 2 would be false"
  fix_rationale: "N/A diagnose-only — plan-phase gaps should wire editors into preview composition and decide block-reorder UX vs line-schema"
  blind_spots: "Did not run live browser repro; relied on code + UAT screenshot description matching code paths"
  candidate_causes:

    - "[code] contextText/schemaText local-only; preview UI omits body/intro; API POST {}"
    - "[config/product] phase never specified drag-reorder topic blocks — only prototype line-schema carry-forward"
  and_gate: "yes — complaint 1 needs dead wiring (code); complaints 2–3 need missing product UI beyond textarea stubs (scope gap) AND same dead wiring so even prototype-equivalent schema lines would not appear"

## Symptoms

expected: |
  On /admin/digest, the intro field («Вводный текст», e.g. «Добрый день коллеги!») is included in «Превью письма».
  «Блоки выпуска» shows the selected topics briefly as blocks whose order can be changed (that order is the publication order).
  The editor can insert optional text blocks between articles as connecting copy; those blocks may also be absent.
actual: |
  User reported (verbatim): "Вводный текст не добавляется в превью письма. Схема дайджеста -> Блоки выпуска Должны отображать выбранные темы кратко (как блоки, положение которых можно менять, устанавливая порядок выхода материала) Также нужна возможность добавлять текстовые блоки редактора между статьсями, чтобы был связующий статьи тект (Но может и отсутствовать)"
  Screenshot context: preview modal «Превью письма» titled «Digest CDS — превью (2026-09-15)» lists only 1. Building Production RAG Systems 2. pgvector for Enterprise Search 3. Anomaly Detection in Audit Pipelines. Intro «Добрый день коллеги!» is visible in the page field but not in the preview. «Блоки выпуска» panel is empty. Footer says «Превью просмотрено. Можно отправить.»
errors: None reported
reproduction: Test 1 in UAT (.planning/phases/05-admin-digest-publish/05-UAT.md). Live admin on /admin/digest, open letter preview.
started: Discovered during UAT of phase 05-admin-digest-publish

## Eliminated

- hypothesis: "Backend returns intro but SPA fails to display only a render bug"
  evidence: "preview_digest_email builds body from titles only with no intro parameter; POST body is '{}'; SPA never reads emailModal.preview.body either — dual omission, not display-only"
  timestamp: 2026-09-21T17:50:00Z

- hypothesis: "«Блоки выпуска» is empty because approved topics failed to load"
  evidence: "Shortlist rows and preview list show three titles; schema panel is an independent empty textarea with no binding to approvedReady"
  timestamp: 2026-09-21T17:50:00Z

## Evidence

- timestamp: 2026-09-21T17:47:00Z
  checked: ".planning/debug/knowledge-base.md"
  found: "File absent — no prior KB match"
  implication: "No known-pattern shortcut; investigate from UI-SPEC + code"

- timestamp: 2026-09-21T17:48:00Z
  checked: "05-UI-SPEC.md Digest editors + Email preview; 05-04-PLAN assumption"
  found: "Editors are in-session inputs that must feed email preview composition; plan assumption 'feed preview composition locally'"
  implication: "Intro-in-preview is contracted phase-5 behavior, not a new wish-list only"

- timestamp: 2026-09-21T17:49:00Z
  checked: "web/src/pages/AdminDigestPage.jsx"
  found: "contextText/schemaText useState only; openEmailPreview → previewEmail() no args; modal renders subject + items.map only; «Блоки выпуска» is free-text textarea starting empty — no reorder UI, no auto-fill from approved topics, no insert-block controls"
  implication: "Complaint 1 = missing wiring/render; complaints 2–3 = missing product UI + same dead field"

- timestamp: 2026-09-21T17:50:00Z
  checked: "web/src/services/adminApi.js previewEmail; backend preview_digest_email.py; admin route POST"
  found: "Mock/live preview return subject/body/items from approved∩ready titles only; live fetch body '{}'; no intro/schema fields on request or DigestPreviewItem"
  implication: "API contract never modeled editorial intro/schema composition"

- timestamp: 2026-09-21T17:51:00Z
  checked: "design-frontend pages/admin-digest.html + scripts/app.js renderEmailPreview"
  found: "Prototype puts context into #email-preview-context; schema is line-based with {{articles}} placeholder and free-text lines as connecting blocks — not drag-reorder topic cards. Articles come from checked ready rows"
  implication: "Phase SPA copied editor chrome labels but omitted prototype preview composition; user reorderable-topic UX exceeds both SPA and prototype"

- timestamp: 2026-09-21T17:51:30Z
  checked: "05-REVIEW.md IN-01"
  found: "Already documented: contextText/schemaText never reach preview or send; stub email ignores them"
  implication: "Known gap from code review; UAT G-05-1 is the user-facing confirmation"

- timestamp: 2026-09-21T17:52:00Z
  checked: "tests/ for contextText/schema/Вводный"
  found: "No tests asserting intro or schema appear in email preview"
  implication: "Why not caught — no gate for editor→preview composition"

## Resolution

root_cause: |
  Three related causes (AND-gate):
  (1) BUG vs phase-5 contract — «Вводный текст» (`contextText`) is session-local dead state: never passed to `previewEmail`/`sendDigest`, never rendered in the preview modal (which lists only server `items`), while UI-SPEC/05-04 required editors to feed preview composition. Backend `preview_digest_email` also builds body from titles only and accepts no intro.
  (2) NEVER IMPLEMENTED — «Блоки выпуска» is an empty free-text textarea, not a list of selected topics as reorderable blocks; nothing auto-populates or reorders publication order from that panel (order is shortlist rank only).
  (3) NEVER IMPLEMENTED as block UI / UNWIRED vs prototype — optional connecting copy exists only as the inert `schemaText` textarea (prototype used one-line-per-block + `{{articles}}` wired into preview); SPA has no insert-between-articles controls and does not compose schema lines into the preview.
fix: ""
verification: ""
files_changed: []
oracle_type: derived
classification:
  complaint_1_intro_in_preview: bug_against_existing_phase5_behavior
  complaint_2_reorderable_topic_blocks: never_implemented
  complaint_3_inter_article_text_blocks: never_implemented_as_block_ui_plus_unwired_prototype_line_schema
