# Phase 23 — External API Coverage

**Detected:** false

**No external API integration:** stores YouTube channel/playlist canonical ids in Postgres only; no Data API, RSS, yt-dlp, or handle/URL resolution (ADR-0002). Enumeration is Phase 24.

Details (not part of the gate declaration):

- CRUD via `IngestSourceRepository`; local regex + kind match (D-14/D-06).
- Does **not** call YouTube Data API v3, Atom/RSS, `google-api-python-client`, or `yt-dlp`.
- ADR-0002 / REQUIREMENTS forbid Data API and `@handle`/URL resolution here.

| Surface | External call? | Notes |
|---------|----------------|-------|
| `POST/PATCH/DELETE/GET /admin/ingest-sources` | No | Validates and persists ids only |
| SPA `ingestSourcesApi.js` | No | Bearer admin HTTP only |
| «Открыть на YouTube» link | No (browser navigation) | Static URL built from stored validated id + fixed path prefixes |
| Migration `012` / Supabase adapter | No YouTube | Postgres via existing service_role client |

---

*Phase: 23-admin-managed-ingest-sources*
