---
status: resolved
resolved:
  at: 2026-10-13
  evidence: "Dialog close stays outside overflow-y-auto with cursor-pointer; locked by a 1280x400 Playwright viewport proof (v1.2 Phase 13)"
trigger: "G-13-1/G-13-2/G-13-3: material and email preview modal close (✕) scrolls away with content; cursor:pointer missing. find_root_cause_only."
created: 2026-10-03T08:10:00Z
updated: 2026-10-03T08:20:00Z
audit_acknowledged:
  milestone: v1.2
  at: 2026-10-05
  status: diagnosed
---

## Current Focus

```yaml
reasoning_checkpoint:
  hypothesis: "G-13-1, G-13-2, and G-13-3 share one layout cause: the ✕ button is a static flex child inside the modal panel that is itself the scrollport (max-h-[90vh] overflow-y-auto), with no sticky/fixed header. Separately, those buttons omit cursor-pointer and Tailwind v4 preflight plus index.css never set cursor:pointer on button, so the UA cursor stays default."
  confirming_evidence:
    - "AdminItemPreview panel at AdminDigestPage.jsx:915 is overflow-y-auto; close button at :920-927 is inside it and has no sticky/fixed classes."
    - "Email preview panel at AdminDigestPage.jsx:785 is the same overflow-y-auto shell; close button at :790-797 is inside it with the same classes."
    - "web/node_modules/tailwindcss/preflight.css button rules (243-257, 377-381) set font/appearance only; the only cursor mention is a comment at 384. web/src/index.css has no button cursor rule."
  falsification_test: "A sticky/fixed class on the close or its header row, or the header rendered outside the overflow-y-auto element, would refute the scroll-away cause. A cursor-pointer class or a base-layer button { cursor: pointer } rule would refute the cursor finding."
  fix_rationale: "Not applied (find_root_cause_only). The scroll fix must keep the close control in the scrollport's sticky header or outside the scrolling region. The cursor fix must add cursor-pointer (or an equivalent base rule) on the close button."
  blind_spots: "Computed style was not measured in a browser; cursor:default is inferred from UA + absent author/preflight cursor rules. Confirm-send dialog uses the same button classes but is not in these gaps."
  candidate_causes:
    - "code: close JSX lives inside the overflow-y-auto panel with no position utility"
    - "config: Tailwind v4 preflight dropped the v3 button cursor:pointer reset, and this app did not restore it"
  and_gate: "no for the three scroll gaps — one layout condition is sufficient. The missing pointer cursor is an independent second defect on the same buttons, not required for the scroll-away."
bug_class: Bohrbug
known_pattern_candidate: none (no .planning/debug/knowledge-base.md)
```

hypothesis: confirmed — close scrolls away because it is inside the overflow panel; cursor is default because nothing sets pointer.
test: done (source + Tailwind preflight)
expecting: n/a
next_action: return diagnosis; do not edit production code

## Symptoms

expected: Material preview close (✕) stays sticky top-right at all scroll positions and uses CSS cursor:pointer. Body scrolls inside the dialog while close remains usable. Email preview close stays sticky in the modal header.
actual: Close scrolls away with content on material preview (tests 1 and 2) and email preview (test 3). User must scroll back to the top to close. User also reports close needs cursor:pointer.
errors: none (behavioral UAT gaps)
reproduction: Open admin material preview with a long markdown body and scroll; open email preview modal and scroll. Close (✕) leaves the viewport.
started: Phase 13 UAT 2026-10-03

## Eliminated

- hypothesis: Document/page scroll (not the dialog) moves the close control.
  evidence: Both overlays are `fixed inset-0`. The scrollport is the inner panel (`max-h-[90vh] overflow-y-auto`). Body-scroll-inside-dialog passing in Test 2 matches that inner scrollport. The close is a child of it, so it moves with dialog content, not the page.
  timestamp: 2026-10-03T08:18:00Z

- hypothesis: Material and email previews use different close implementations, so they cannot share one cause.
  evidence: Both are inline in AdminDigestPage.jsx with the same panel classes and the same close button classes. There is no separate AdminEmailPreview component.
  timestamp: 2026-10-03T08:18:00Z

## Evidence

- timestamp: 2026-10-03T08:14:00Z
  checked: web/src/pages/AdminDigestPage.jsx AdminItemPreview
  found: Lines 915-927. Panel `className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-2xl bg-paper p-6"` wraps a static header row and the ✕ button `className="inline-flex min-h-11 min-w-11 items-center justify-center"`. No sticky, fixed, or cursor-pointer. Markdown body (937-946) is a later sibling inside the same scrollport.
  implication: G-13-1 and G-13-2. Long markdown increases panel scroll height; the header including ✕ scrolls out. Body scroll "pass" is this same overflow-y-auto.

- timestamp: 2026-10-03T08:14:00Z
  checked: web/src/pages/AdminDigestPage.jsx email preview modal
  found: Lines 785-797. Identical panel classes and identical close button classes. Subject, iframe, and item list are siblings below the header, all inside overflow-y-auto.
  implication: G-13-3 is the same layout bug copied onto the email dialog, not a second mechanism.

- timestamp: 2026-10-03T08:16:00Z
  checked: Tailwind 4.3.3 preflight and web/src/index.css
  found: package.json devDependency tailwindcss ^4.3.3. preflight.css button block at 243-257 sets font, color, border-radius, background, opacity only. Second button block at 377-381 sets appearance:button. Grep of preflight.css finds no `cursor:` property. index.css @import "tailwindcss" and has no button cursor rule. Repo-wide web/src cursor-pointer exists only on RazborPage and MaterialPage `<summary>`, not on these buttons.
  implication: Author and Tailwind preflight leave the close button on the browser default cursor (default), which matches the UAT cursor:pointer observation.

## Resolution

root_cause: The material preview (AdminItemPreview) and email preview modals put the ✕ control inside the scrolling panel (`overflow-y-auto` + `max-h-[90vh]`) as a non-sticky flex item, so it scrolls away with the body. Independently, the close button classes omit `cursor-pointer`, and Tailwind v4 preflight plus index.css do not set `cursor: pointer` on buttons, so the cursor stays the UA default.
fix:
verification:
files_changed: []
