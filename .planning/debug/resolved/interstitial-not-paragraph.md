---
status: resolved
resolved:
  at: 2026-10-13
  evidence: "Interstitial p/br matrix ships in render_email_html; Playwright asserts paragraph breaks (v1.2 Phase 13)"
trigger: "Gap G-13-3c (test 3, minor): interstitial connecting text «Связывающий текст - тест» renders flat in the email iframe; expected <p> per ADUX-03 / Phase 12 interstitial_html. Goal: find_root_cause_only."
created: 2026-10-03T11:14:00+03:00
updated: 2026-10-03T11:25:00+03:00
audit_acknowledged:
  milestone: v1.2
  at: 2026-10-05
  status: diagnosed
---

## Current Focus

hypothesis: Connecting text is already emitted as a single `<p>` by render_interstitial_html. The flat iframe look is an unstyled srcdoc fragment (no email CSS), not missing paragraph markup. A one-line string has no `\n\n`, so ADUX-03 correctly produces one paragraph.
test: Read render_interstitial_html, render_email_html text-block branch, preview wiring, iframe srcDoc, and parent CSS scope.
expecting: HTML fragment contains `<p>…</p>` for interstitial text; no `<div>`, no escaped literal tags, no raw unwrapped string. Parent stylesheet does not enter the iframe.
next_action: Return ROOT CAUSE FOUND. Do not edit production code.
bug_class: Bohrbug
known_pattern_candidate: none (no .planning/debug/knowledge-base.md)

reasoning_checkpoint:
  hypothesis: "render_interstitial_html wraps interstitial/intro text in <p> after html.escape; a single-line connecting string becomes one <p>, so the iframe shows a paragraph that looks flat because the srcdoc fragment has no email stylesheet."
  confirming_evidence:
    - "email_render.py:15-27 builds `<p>` + escaped text + `</p>` per blank-line split; single newline becomes `<br>` inside that `<p>`."
    - "render_email_html lines 62-65 call that helper for kind==text; preview_digest_email.py:136 and :191-194 pass PreviewTextBlock.text into it."
    - "AdminDigestPage.jsx:826 sets srcDoc to preview.html with no rewrite. Parent index.css only sets body { margin: 0 } and does not load inside the iframe."
    - "Unit contract: test_render_interstitial_html_single_paragraph expects `<p>hello</p>`; test_preview_html_present_with_interstitial_paragraphs expects `<p>Bridge A</p><p>Bridge B</p>`."
  falsification_test: "A preview HTML string for kind=text that contains the connecting copy outside `<p>…</p>`, or as a `<div>`, or as escaped `&lt;p&gt;` text."
  fix_rationale: "No markup fix. ADUX-03 is the tag split, already implemented. Visual flatness of one unstyled paragraph is outside that contract (13-VALIDATION.md: pixel spacing is subjective / polish-only)."
  blind_spots: "Did not open the live iframe in a browser; conclusion is from the render path and the srcdoc boundary, not a captured DOM snapshot of this UAT session."
  candidate_causes:
    - "code: interstitial HTML omitted `<p>` (eliminated)"
    - "config/environment: parent CSS reset zeroed iframe paragraph margins (eliminated — iframe document does not include index.css)"
  and_gate: "no — one condition explains the report: correct single `<p>` in an unstyled srcdoc. Markup and CSS-reset are not both required."

## Symptoms

expected: Interstitial connecting text in email HTML renders as a paragraph (`<p>`) per ADUX-03 / Phase 12 interstitial_html contract.
actual: "Связывающий текст - тест" renders flat inside the email iframe.
errors: none
reproduction: Admin digest email preview iframe; connecting-text block with that single-line string.
started: UAT test 3, gap G-13-3c (2026-10-03).

## Eliminated

- hypothesis: Connecting text is inserted as a raw string, an escaped `&lt;p&gt;` literal, or a `<div>` without paragraph markup.
  evidence: render_interstitial_html returns joined `<p>` elements; text blocks go through that helper only. No other email HTML composer in the preview path.
  timestamp: 2026-10-03T11:20:00+03:00

- hypothesis: Phase 12 interstitial_html differs and the preview path bypasses it.
  evidence: Phase 12 tree has no interstitial_html. The function is Phase 13 D-13 in backend/src/backend/application/use_cases/email_render.py. Preview and send both call render_email_html.
  timestamp: 2026-10-03T11:21:00+03:00

- hypothesis: Parent `body { margin: 0 }` flattens paragraphs inside the iframe.
  evidence: The rule is on the parent document body (web/src/index.css:40-42), not on `p`, and srcDoc is a separate document. Email HTML includes no `<style>` that zeros `p` margins.
  timestamp: 2026-10-03T11:22:00+03:00

## Evidence

- timestamp: 2026-10-03T11:18:00+03:00
  checked: .planning/debug/knowledge-base.md
  found: File absent. No prior resolution to test first.
  implication: Open investigation.

- timestamp: 2026-10-03T11:19:00+03:00
  checked: backend/src/backend/application/use_cases/email_render.py render_interstitial_html
  found: strip → html.escape → split on `\n\n` → each non-empty part wrapped in `<p>`, internal `\n` replaced with `<br>`. Empty/whitespace returns "".
  implication: A one-line string is exactly one paragraph element, not unwrapped text.

- timestamp: 2026-10-03T11:19:00+03:00
  checked: render_email_html text and intro branches; preview_digest_email._html_content_blocks and preview_digest_email; send_digest body_html
  found: Intro and kind=="text" both use render_interstitial_html. PreviewTextBlock.text is copied into {"kind":"text","text": block.text}. Send uses the same renderer.
  implication: Live preview HTML for «Связывающий текст - тест» is `<p>Связывающий текст - тест</p>` (plus sibling material blocks).

- timestamp: 2026-10-03T11:20:00+03:00
  checked: web/src/pages/AdminDigestPage.jsx iframe; web/src/services/adminApi.js composeMockInterstitialHtml; web/src/index.css
  found: iframe srcDoc={emailModal.preview.html} with empty sandbox and no HTML rewrite. Mock helper maps the same way to `<p>`. Parent CSS does not style iframe contents. Email fragment has no stylesheet.
  implication: Flat look is unstyled UA paragraph rendering of a single `<p>`, not a missing tag. User-agent `p` margins still apply.

- timestamp: 2026-10-03T11:21:00+03:00
  checked: ADUX-03 / D-13 / 13-VALIDATION.md manual row
  found: Contract is `\n\n` → `<p>` (and single `\n` → `<br>`). Validation says the unit matrix covers the tags; visual spacing in the iframe is subjective and polish-only.
  implication: Gap truth is already met by markup. No code change.

## Resolution

root_cause: Not a markup defect. Interstitial connecting text is emitted as `<p>` by render_interstitial_html (email_render.py:15-27), applied to intro and kind=text blocks (email_render.py:55-65), and placed unchanged in the preview iframe srcDoc (AdminDigestPage.jsx:821-826). The reported string has no blank line, so the contract yields one paragraph, `<p>Связывающий текст - тест</p>`. The flat appearance is that unstyled srcdoc fragment (no email `<style>`); parent CSS does not enter the iframe and does not zero `p` margins. Phase 12 has no interstitial_html function; the contract is Phase 13 D-13 / ADUX-03.
fix: none (find_root_cause_only; markup already matches the contract)
verification: static trace of renderer, preview/send wiring, iframe srcDoc, and unit assertions test_render_interstitial_html_single_paragraph and test_preview_html_present_with_interstitial_paragraphs. No production edit.
files_changed: []
oracle_type: specified
guardrail_verdict: n/a (no fix applied)
