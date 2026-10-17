# Phase 23 — External API Coverage

**Detected:** false

**No external API integration:** This phase CRUD-stores admin-managed YouTube channel/playlist *canonical ids* in Postgres behind `IngestSourceRepository`. It does **not** call YouTube Data API v3, Atom/RSS feeds, `google-api-python-client`, or `yt-dlp`. Canonical-id validation is local regex + kind match (D-14/D-06). Enumeration and scheduling are Phase 24 (`ING-02`+). ADR-0002 / REQUIREMENTS forbid Data API and `@handle`/URL resolution here.

| Surface | External call? | Notes |
|---------|----------------|-------|
| `POST/PATCH/DELETE/GET /admin/ingest-sources` | No | Validates and persists ids only |
| SPA `ingestSourcesApi.js` | No | Bearer admin HTTP only |
| «Открыть на YouTube» link | No (browser navigation) | Static URL built from stored validated id + fixed path prefixes |
| Migration `012` / Supabase adapter | No YouTube | Postgres via existing service_role client |

---

*Phase: 23-admin-managed-ingest-sources*
