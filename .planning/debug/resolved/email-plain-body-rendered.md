---
status: resolved
resolved:
  at: 2026-10-13
  evidence: "Email preview success view is subject + sandboxed iframe only; the numbered preview.items list is unmounted (v1.2 Phase 13)"
trigger: "Gap G-13-3b (test 3, major): Email preview modal shows a numbered plain-text list under the iframe, duplicating HTML email content. Plain body must stay internal."
created: 2026-10-03T11:12:00+03:00
updated: 2026-10-03T11:20:00+03:00
goal: find_root_cause_only
bug_class: Bohrbug
audit_acknowledged:
  milestone: v1.2
  at: 2026-10-05
  status: diagnosed
---

## Current Focus

hypothesis: The numbered list under the iframe is the leftover `<ul>` that maps `emailModal.preview.items` to `{rank}. {title}`. `preview.body` is not mounted.
test: Read email-modal JSX, preview DTO composers, D-10, and UI-SPEC email display contract.
expecting: Visible text `1. {title}` comes from items.rank/title; `preview.body` uses `- {title}` and has no render site in the modal.
next_action: Return diagnosis. Do not edit production code.
known_pattern_candidate: none (no `.planning/debug/knowledge-base.md`)

reasoning_checkpoint:
  hypothesis: "AdminDigestPage email modal renders a user-visible `<ul>` of `preview.items` (`{rank}. {title}`) under the sandboxed iframe. That list is the duplicate numbered titles. Plain `preview.body` is composed for logs/text clients and is not written into the modal DOM."
  confirming_evidence:
    - "web/src/pages/AdminDigestPage.jsx:832-838 maps emailModal.preview.items into <li>{row.rank}. {row.title}</li> directly under the iframe, with no hide/toggle."
    - "composePreviewItems assigns rank as 1-based composition position, so the text is exactly '1. {title}', '2. {title}'."
    - "composePreviewBody emits dash bullets (`- {title}`), and the modal never reads preview.body. Playwright only asserts email-preview-body count 0 (tests/admin.spec.js:567), which this <ul> does not use."
    - "D-10 and 13-UI-SPEC email display: UI renders html only; subject stays above the iframe; plain body is not a user-visible surface. Plan 13-04 key-decision kept this secondary <ul> anyway."
  falsification_test: "If the list text were preview.body, the DOM would show dash-prefixed lines or a body string/testid, and removing the items <ul> would leave the numbered list. Neither is true."
  fix_rationale: "Stop rendering the items <ul> in the success branch (html iframe + subject only). Optional HTML/Plain toggle is not required to meet the lock."
  blind_spots: "Did not re-run the live admin UI in a browser this session; diagnosis is from the render path that always paints items when the preview DTO is shown."
  candidate_causes:
    - "code: leftover items <ul> in AdminDigestPage email modal (13-04 kept it for rank/title asserts)"
    - "data: preview.items is still populated — allowed by D-10; empty items would hide the symptom without removing the render"
  and_gate: "no — DTO items are in-contract. The failure is the unconditional user-visible render. Both are present at runtime, but only the JSX violates the lock."

## Symptoms

expected: Email preview modal shows HTML in the iframe only. Plain `body` is internal (stub logs, text clients, debug) and must not render as a duplicate numbered list under the iframe.
actual: Under the iframe, the modal renders a numbered plain-text list (1. Обвязка важнее модели… 2. Децентрализованный AI…) that duplicates the HTML email content already inside the iframe.
errors: none (visual contract violation)
reproduction: Open admin digest email preview (Превью письма) with at least two approved ready materials. HTML iframe is correct; a numbered title list appears beneath it.
started: Present after Phase 13 email honesty (iframe added; items list kept). UAT test 3, gap G-13-3b.

## Eliminated

- hypothesis: The modal renders the plain `preview.body` string (or `email-preview-body`) under the iframe.
  evidence: Success branch renders subject, optional iframe `srcDoc={preview.html}`, then `preview.items` only. No `preview.body` read. `composePreviewBody` format is `- {title}`, not `1. {title}`. Playwright expects `email-preview-body` count 0 and that testid is absent from the modal.
  timestamp: 2026-10-03T11:18:00+03:00

- hypothesis: Material preview markdown (`AdminItemPreview` / `body_markdown`) is the duplicate list.
  evidence: That modal is a separate dialog (`previewItem`). The numbered list sits in the email dialog success branch (`emailModal.preview.items`).
  timestamp: 2026-10-03T11:18:00+03:00

## Evidence

- timestamp: 2026-10-03T11:14:00+03:00
  checked: `.planning/debug/knowledge-base.md` and active debug files
  found: No knowledge base. No prior session for this gap.
  implication: No known-pattern shortcut.

- timestamp: 2026-10-03T11:15:00+03:00
  checked: `web/src/pages/AdminDigestPage.jsx` email modal (approx. 778-843)
  found: After the iframe, an unconditional `<ul className="mt-4 space-y-2">` maps `emailModal.preview.items` to `{row.rank}. {row.title}` (lines 832-838).
  implication: This is the numbered list under the iframe. It is always shown when a preview DTO is open.

- timestamp: 2026-10-03T11:16:00+03:00
  checked: `web/src/services/adminPreviewComposition.js` `composePreviewItems` / `composePreviewBody`
  found: Items get `rank` = 1-based position and `title`. Body is a newline string of optional intro plus `- {title}` lines. Mock `previewEmail` returns both; live path returns the API DTO (`body`, `html`, `items`).
  implication: User-visible `1. Title` matches items, not body.

- timestamp: 2026-10-03T11:17:00+03:00
  checked: `13-CONTEXT.md` D-10 and `13-UI-SPEC.md` email preview display (lines 150-180)
  found: D-10 — UI renders `html` only; plain `body` stays for StubMailer logs / text-only / debug; `subject` / `items` stay on the response as needed. UI-SPEC — iframe is the email surface; do not show plain body to users (default hide); subject stays above the iframe. No items list in the email modal contract.
  implication: Rendering `items` as a second title list violates the lock. Keeping `items` on the DTO does not.

- timestamp: 2026-10-03T11:17:00+03:00
  checked: `13-04-SUMMARY.md` key-decisions
  found: "Keep secondary items <ul> under iframe for existing rank/title list asserts; honesty surface is iframe only" and pattern "subject → iframe → optional items list".
  implication: The duplicate list was left in on purpose during 13-04. The honesty e2e only checks the iframe and that `email-preview-body` is absent, so this `<ul>` stayed green.

- timestamp: 2026-10-03T11:18:00+03:00
  checked: common bug patterns
  found: Dual source of truth — same titles painted in iframe HTML and again from `preview.items`. Deterministic (Bohrbug). Not null access, async, or env.
  implication: Single render-site defect.

## Resolution

root_cause: The email preview success branch in AdminDigestPage.jsx unconditionally renders `emailModal.preview.items` as a visible `<ul>` of `{rank}. {title}` under the sandboxed HTML iframe. `composePreviewItems` numbers those rows from 1, so the modal shows a second title list beside the HTML that already contains the same titles. Plain `preview.body` is not rendered (it stays on the DTO for logs/text/debug, per D-10). Plan 13-04 kept this list for rank/title asserts; UI-SPEC and D-10 require the user-visible preview to be the iframe (plus subject above it).
fix: 
verification: 
files_changed: []
oracle_type: specified
guardrail_verdict: 
