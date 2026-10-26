# Phase 22 — External API Coverage

**Declared:** 2026-10-17
**Detector disposition:** No external API integration

## Reasoned exemption

Phase 22 (ADUX-12 / backlog 999.5) regroups SPA navigation chrome only:

- Remove the AppShell top-level «Пайплайн» pill; keep one «Админ» → `/admin/digest`.
- Add pathless `AdminLayout` with in-page «Дайджест | Пайплайн» and nest digest/pipeline under it.
- Amend Playwright tripwires and supersede `16-UI-SPEC` A-2 text.

There is **no** new HTTP client, SDK, webhook, third-party registry call, or backend route change. Existing admin APIs (`pipelineConfigApi`, digest shortlist, etc.) are untouched. A fake coverage matrix would invent endpoints that this phase does not call.

**Coverage matrix:** not applicable — frontend route/chrome regrouping only.
