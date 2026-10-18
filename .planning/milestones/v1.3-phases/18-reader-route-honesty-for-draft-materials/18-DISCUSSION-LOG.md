# Phase 18: Reader-route honesty for draft materials - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-14
**Phase:** 18-reader-route honesty for draft materials
**Areas discussed:** Preview surface, Preview marker & caching, Draft related/tags exposure, Admin/email link target, Response DTO shape, Admin gate, Status coverage, `ready` status handling

---

## Preview surface

| Option | Description | Selected |
|--------|-------------|----------|
| Dedicated admin route | New admin route (e.g. `/admin/materials/:slug`) behind a new admin-gated endpoint; reader route + `get_material_for_reader` untouched | ✓ |
| Reader-flagged variant | Admin-flagged variant of the reader route (e.g. `/materials/:slug?preview=1`) reusing `MaterialPage` | |
| Reuse in-page admin preview | Reuse the existing admin-digest in-page preview — no new route | |

**User's choice:** Dedicated admin route
**Notes:** Rationale recorded in CONTEXT.md D-01 — the criterion demands the *normal reader rendering*, and the reader route must stay byte-identical.

---

## Preview marker & caching

| Option | Description | Selected |
|--------|-------------|----------|
| Sticky banner | Persistent banner above the article + `no-store` on the response | ✓ |
| Inline badge | Badge in the article header next to the title + `no-store` | |
| Chrome-only marker | Marker only in the admin page chrome / toolbar + `no-store` | |

**User's choice:** Sticky banner
**Notes:** Banner copy proposed: «Черновик — предпросмотр, не опубликовано». Marker must travel with the article body, not the page chrome.

---

## Draft related/tags exposure

| Option | Description | Selected |
|--------|-------------|----------|
| Omit both | Hide `related` and `tags` entirely while unpublished | ✓ |
| Filter to ready | Render both, filtered to ready/published only | |
| Tags only | Render `tags`, omit `related` (or vice-versa) | |

**User's choice:** Omit both
**Notes:** Simplest honest surface, zero unpublished leakage (criterion 3).

---

## Admin/email link target

| Option | Description | Selected |
|--------|-------------|----------|
| Repoint + `_blank` | Repoint «Открыть материал →» at the admin preview URL, open with `target="_blank" rel="noopener noreferrer"` to escape `sandbox=""` | ✓ |
| `postMessage` bridge | Keep the link, add a `postMessage` bridge from the sandboxed iframe to the parent SPA | |
| Backend admin redirect | Keep reader-route links, add an admin-only redirect when the slug is a draft | |

**User's choice:** Repoint + `_blank`
**Notes:** Chosen because the sandboxed iframe cannot navigate the top-level app itself. Admin shortlist link repointed at the same destination (D-10).

---

## Response DTO shape

| Option | Description | Selected |
|--------|-------------|----------|
| Same DTO | Return exactly the `GET /materials/{slug}` DTO; render with the same page component | ✓ |
| Separate preview DTO | Distinct preview DTO carrying a marker field (e.g. `preview: true`) | |

**User's choice:** Same DTO
**Notes:** Makes "normal reader rendering" structural rather than an imitation.

---

## Admin gate

| Option | Description | Selected |
|--------|-------------|----------|
| `require_admin` | DB-role check (`profiles.role=admin`), same as every `/admin/*` route | ✓ |
| JWT app-role claim | App-role claim in the JWT without a DB lookup | |

**User's choice:** `require_admin`
**Notes:** Keeps a single admin gate mechanism.

---

## Status coverage

| Option | Description | Selected |
|--------|-------------|----------|
| Draft + ready | Admin opens any pre-publication material; marker when status is not published | |
| Draft only | Only `draft`; `ready` is already reachable at the reader route | ✓ |

**User's choice:** Draft only
**Notes:** Follow-up was needed — see the `ready` status row below.

---

## What the preview does with a published material

| Option | Description | Selected |
|--------|-------------|----------|
| Always serve | Serve the material at any status, single behaviour | |
| Redirect | Redirect to the public reader route when published | ✓ |

**User's choice:** Redirect
**Notes:** Consistent with the `draft`-only decision.

---

## `ready` status handling (clarification round)

| Option | Description | Selected |
|--------|-------------|----------|
| `ready` → reader | `ready` is readable at the reader route, so preview redirects there | ✓ |
| `ready` → preview | `ready` opens in preview like `draft` | |
| Strict `draft` only | Only `draft` previews; `ready` and `published` both redirect | |

**User's choice:** `ready` → reader route redirect
**Notes:** This resolved a conflict between the "draft only" answer and the ROADMAP goal's "any draft (or ready) material" wording — a `ready` material is readable, just at the reader route, so the goal holds without giving `ready` a preview-specific path. The "strict draft only" option is behaviourally equivalent to the chosen one; the chosen label records *why* `ready` is not a preview case.

---

## Claude's Discretion

- Exact route path / HTTP shape for the new admin endpoint and which router file it lands in.
- Exact banner copy and its placement within the existing reader layout (must be persistent and above the article body).
- Whether `no-store` is set at the endpoint or via a route dependency.

## Deferred Ideas

None — discussion stayed within phase scope.
