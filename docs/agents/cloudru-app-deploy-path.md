# Cloud.ru app deploy path (documented only)

**Phase 1 does not deploy** FastAPI or the SPA to a Cloud.ru application VM (D-07 / PLAT-08). This document outlines the **future** path so operators know how production-shaped hosting will look after the local foundation is green.

Supabase itself already runs on a **separate** self-hosted VM ([ADR-0004](../adr/0004-self-hosted-supabase-on-vm.md)). App processes (API + static web) are expected later on a Cloud.ru app VM in the same contour as FoundryModels-oriented workloads ([ADR-0002](../adr/0002-cloud-ru-foundrymodels-deployment.md)) — without expanding the ML pipeline scope here.

---

## What Phase 1 delivers instead

- Local FastAPI + Vite against remote Supabase — see [`local-platform-runbook.md`](./local-platform-runbook.md).
- Env templates and CORS allowlists suitable for localhost origins.
- No live `systemctl` / container rollout of Digest CDS app processes in this phase.

---

## Future app VM shape (outline)

| Concern | Direction |
|---------|-----------|
| Process manager | systemd unit(s) or equivalent for `uvicorn` FastAPI factory (`create_default_app`) and a static file server / reverse proxy for the Vite `web/dist` build |
| Env injection | Same names as [`.env.example`](../../.env.example); inject via host env or a secret store — **never** bake `SUPABASE_SECRET_KEY` into images or git |
| CORS | Set `API_CORS_ORIGINS` to the real HTTPS SPA origin(s) on the app host (replace localhost:5173/5174) |
| Supabase | Keep pointing at the existing knowledge-db.ru (or successor URL) — app VM is not a second database |
| `APP_CONTAINER` | `live` in deployed environments so `/me/ping` persists to `activity_events` |
| Reverse proxy | Terminate TLS; forward `/api` (or chosen prefix) to uvicorn; serve SPA assets |
| Secrets | Host secret manager / sealed files outside the repo; rotate without rebuilding domain code |

---

## Explicit non-goals for Phase 1

- No SSH deploy automation, no CI push-to-VM, no Docker Compose for the **app** stack in this phase.
- No FoundryModels pipeline rollout (ADR-0002 contour only).
- No committing production secrets into the repository or container layers (T-01-13).

When Phase 1 local live proof is approved, a later phase/plan can turn this outline into concrete unit files and a checked-in deploy runbook with real hostnames.
