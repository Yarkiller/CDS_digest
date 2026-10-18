# Context (from DOCs)

## Product overview — Digest CDS
- source: docs/digest-cds/project_description.md
- Product Digest CDS for CDS (Chief Data Science) in Sberbank SVA. UI concept v1: Concept 3 Editorial UI («Digest CDS: издание»). Collects/structures/distributes tech knowledge: external video/text → source text via FoundryModels on Cloud.ru → agent-prepared article → knowledge card, weekly digest, voting→razbor cycle. Video/audio never stored or shown as material. Personas: рядовой сотрудник СВА, Data Analyst, Data Scientist, Админ (CDS/делегат). Access only `@sberbank.ru` / `@omega.sbrf.ru`. v1 features: login, issue, materials, voting, knowledge, razbory, admin shortlist/send, archive. Post-v1 out of core: quiz cards, YAML pipeline UI, public leaderboard.

## Personas and journeys (Concept 3)
- source: docs/digest-cds/user_stories.md
- Four personas with distinct Sber roles (Data Analyst ≠ Data Scientist). Journeys J1–J6: weekly issue, vote, analyst KB, scientist razbor, admin send, corporate login. Backbone maps activities to US-01…US-31 (21 Must / 6 Should / 4 Nice). v1 excludes XP, streak, public leaderboard, quizzes. Material = agent-prepared article only.

## UI backlog closure registry
- source: docs/digest-cds/backlog_UI.md
- GhostUser findings C3-01…C3-18 against design-frontend static prototypes marked FIXED as of 2026-08-30. Closure of static prototype gaps is not a substitute for production QA/backend/access checks. Severity legend HIGH/MEDIUM/LOW; types UX/QA/CONTENT/IA.

## Development report pointer
- source: docs/digest-cds/development_report.md
- Stub pointing to canonical repo-root `development_report.md` for homework submission.

## Domain docs consumption for agents
- source: docs/agents/domain.md
- Before exploring: read CONTEXT.md (or CONTEXT-MAP.md), then relevant docs/adr/. Use glossary vocabulary; flag ADR conflicts explicitly rather than silently overriding. Missing CONTEXT/ADR files → proceed silently.

## Issue tracker conventions
- source: docs/agents/issue-tracker.md
- Issues/specs live under `.scratch/<feature>/`: spec.md, issues/NN-slug.md, Status: triage, Comments section. Wayfinder map.md + child tickets with Type/Status/Blocked-by; claim/resolve protocol.

## Git remote origin via WSL
- source: docs/agents/git-origin.md
- Default remote `origin` (Cursor Origin). All origin push/pull/fetch/auth must run via WSL, not PowerShell. Local status/diff/add/commit without push may use PowerShell. Do not commit credentials or put API keys in mcp.json/.env/rules.

## AI session notes (homework Steps 5–6)
- source: docs/digest-cds/ai_session_notes.md
- Working appendix: header SearchPill modal removed for enlarged inline search; Playwright coverage map for web app; responsive fixes (min-w-0 at 320px). Evidence under responsive-evidence/.

## Responsive evidence catalog
- source: docs/digest-cds/responsive-evidence/README.md
- Playwright screenshots: mobile 320/390 issue, mobile 390 voting, desktop 1280 issue. Assertions: no horizontal overflow; mobile hides identity; desktop shows identity + wider search; voting confirm in viewport on phone.
