# Design — Digest CDS Bubble

A locked design system for the Concept 3 static prototype. Every page shares
this system; page variety comes from information architecture and content
density, not from unrelated themes.

## Genre
playful — restrained, tactile, friendly, and exact

## Macrostructure family
- Marketing pages: none in this prototype.
- App pages: Ecosystem Index — open content surfaces, offset clusters, and
  rounded controls instead of a uniform card wall.
- Content pages: Long Document — comfortable reading measure, clear sections,
  and a persistent reading rail on wide screens.
- Auth pages: Quiet form shell — one task, one visible form, no decorative
  illustration.

## Theme
- `--color-paper`   `oklch(97% 0.012 95)`
- `--color-paper-2` `oklch(93.5% 0.018 95)`
- `--color-ink`     `oklch(20% 0.015 270)`
- `--color-ink-2`   `oklch(43% 0.020 270)`
- `--color-rule`    `oklch(84% 0.018 95)`
- `--color-muted`   `oklch(48% 0.018 270)`
- `--color-accent`  `oklch(52% 0.13 278)`
- `--color-accent-ink` `oklch(98% 0.005 95)`
- `--color-focus`   `oklch(42% 0.14 278)`
- `--color-voting`  `oklch(62% 0.14 38)`
- `--color-voting-ink` `oklch(24% 0.020 38)`

The accent is reserved for links, active states, focus, and small anchors.
Voting and status colours are semantic, not decorative. No gradients or
glass surfaces.

## Typography
- Display: `Bricolage Grotesque`, weight 600, style normal
- Body: `IBM Plex Sans`, weight 400
- Mono: `IBM Plex Mono`, weight 400
- Display tracking: `-0.025em`
- Type scale anchor: `--text-display = clamp(2.25rem, 5vw + 0.75rem, 4.75rem)`
- Long-form measure: `65ch` maximum, line-height 1.65 minimum

## Spacing
4-point named scale:
`--space-2xs`, `--space-xs`, `--space-sm`, `--space-md`, `--space-lg`,
`--space-xl`, `--space-2xl`, `--space-3xl`.

Pages use named tokens only. Controls have a minimum 44px touch target.

## Motion
- Easings: `--ease-out`, `--ease-in`, `--ease-in-out`
- Reveal pattern: no scroll-triggered content reveals
- App interaction: restrained hover colour shift, pressed translate, and
  opacity-only modal feedback
- Reduced-motion fallback: no spatial motion; opacity-only transition ≤150ms

## Microinteractions stance
- Silent success whenever the result is visible
- Toasts only for failures or invisible asynchronous results
- Hover delay 800ms; focus delay 0ms
- Keyboard navigation is equivalent to pointer navigation

## CTA voice
- Primary CTA: compact rounded control, solid accent, one-line verb
- Secondary CTA: outlined rounded control with the same height
- Editorial links: underlined or arrowed text links, never fake buttons

## Navigation and footer
- Navigation: N13 inline search pill with a responsive menu fallback.
- Footer: Ft5 statement — one closing sentence and minimal utility links.
- The prototype gallery keeps its back-link; production screens use one app
  shell, not two stacked navigation bars.

## What pages MUST share
- Digest CDS wordmark and the same font tokens.
- Warm paper surfaces and indigo accent placement.
- 44px interactive targets and visible `:focus-visible` rings.
- The same button, input, modal, status, and mobile navigation language.
- No invented editorial facts, no video-player chrome, and no decorative
  gradients.

## What pages MAY differ
- App pages may vary between index, list, ballot, and admin density.
- Reading pages may use a sticky TOC only when the viewport supports it.
- Admin content stays sans-led while email preview may use display type.

## Exports

### tokens.css
The canonical implementation is [`styles/tokens.css`](styles/tokens.css).
It contains the complete color, font, spacing, type, motion, radius, and
z-index token set.

### Tailwind v4 `@theme`
This static prototype does not use Tailwind. If migrated, map the semantic
tokens from `styles/tokens.css` directly into `@theme`.

### DTCG `tokens.json`
This static prototype does not use DTCG. Preserve the semantic names when
exporting the token values.

### shadcn/ui CSS variables
If the prototype is migrated to shadcn/ui, map paper/ink/accent/rule/focus to
`--background`, `--foreground`, `--primary`, `--border`, and `--ring`.

## Provenance
- Source: Hallmark multi-page redesign of Concept 3
- Mood: bubble-style, clarified by the user
- Scope: visual layer plus obvious prototype interaction and accessibility
  repairs; routes, copy intent, assets, and source documents remain intact.
