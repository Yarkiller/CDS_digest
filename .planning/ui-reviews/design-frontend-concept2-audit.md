# Hallmark audit — design-frontend (Concept 2)

**Scope:** static prototype in `design-frontend/` after applying Concept 2 from `archive/extracted/Homework_by_project/UI_concepts/Concept_2/`.
**Method:** code-only review against `hallmark` anti-pattern list.
**Note:** The audited artefacts are an intentionally requested designer concept (dark-first gamified DS-community UI). Several flagged tells are part of that concept and were kept by explicit requirement.

## Findings

### Critical

1. **Gradient headline** — `pages/login.html:21`
   - `background: linear-gradient(135deg,#8B5CF6,#06B6D4); -webkit-background-clip:text;`
   - Hallmark considers gradient text a strong AI-generated tell.
   - → Fix: use solid `var(--color-primary)` ink for the wordmark.
   - **Kept:** matches the requested Concept 2 auth card styling.

2. **Side-stripe card** — `styles/components.css:84`
   - `.quest-banner { border-left: 3px solid var(--color-xp); ... }`
   - Thick asymmetric coloured border is a listed critical tell.
   - → Fix: full hairline border or a small accent square beside the heading.
   - **Kept:** part of the Concept 2 quest-banner design.

### Major

3. **Purple-gradient primary button** — `styles/components.css:10`
   - `.btn--primary { background: linear-gradient(135deg, #8B5CF6, #6D28D9); }`
   - Purple-gradient controls are close to the purple-gradient-hero tell.
   - → Fix: solid `var(--color-primary)` fill.
   - **Kept:** required by Concept 2 accent system.

4. **Purple-gradient avatar** — `styles/components.css:67`
   - `.avatar { background: linear-gradient(135deg, var(--color-primary), var(--color-accent)); }`
   - Gradient avatars read as generated decorative treatment.
   - → Fix: solid fill or a subtle border ring.
   - **Kept:** part of Concept 2 avatar styling.

### Minor

5. **Placeholder names** — `pages/home.html`, `pages/leaderboard.html`, `pages/profile.html`
   - "Иван Петров", "Anna K.", "Maria S.", etc.
   - → Fix: use plausible domain-specific placeholders if this becomes production content.
   - **Kept:** demo-only static prototype.

## Verdict

**2 critical · 2 major · 1 minor**

The flagged items are stylistic signatures of the requested Concept 2 (purple/cyan accents, gradient headline, XP side-stripe). They are intentionally preserved. No functional regressions were found — `npm run test:design` passes 9/9.
