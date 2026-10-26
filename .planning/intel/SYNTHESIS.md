# Synthesis Summary

Entry point for downstream `gsd-roadmapper`. MODE=`new`. Precedence: ADR > SPEC > PRD > DOC.

## Doc counts by type

| Type | Count |
|------|------:|
| ADR | 4 |
| PRD | 2 |
| SPEC | 2 |
| DOC | 8 |
| UNKNOWN | 0 |
| **Total classified** | **16** |

## Decisions

- Locked: **1** — `docs/adr/0001-public-leaderboard-gamification.md` (public leaderboard deferred past v1)
- Proposed: **3** — ADR-0002 (Cloud.ru + FoundryModels), ADR-0003 (email domains), ADR-0004 (self-hosted Supabase)
- Intel: `.planning/intel/decisions.md`

## Requirements

- Extracted: **31** (`REQ-US-01` … `REQ-US-31`)
- Sources: user stories + acceptance criteria (complementary merge)
- Intel: `.planning/intel/requirements.md`

## Constraints

- Count: **13**
- Type breakdown: protocol 4 · schema 1 · api-contract 2 · nfr 6
- Sources: `technical_specification.md`, `error_handling.md`
- Intel: `.planning/intel/constraints.md`

## Context topics

- Count: **9** topics from DOC sources
- Intel: `.planning/intel/context.md`

## Conflicts

- Blockers: **0**
- Competing variants (WARNINGS): **0**
- Auto-resolved / informational (INFO): **3**
- Detail: `.planning/INGEST-CONFLICTS.md`

## Cycle detection

- Re-verified: **acyclic** (`user_stories` → `acceptance_criteria` → `error_handling`)
- Parent attributions in classification JSON treated as non-edges per source prose
- No UNKNOWN/low-confidence docs

## Status

**READY** — safe to route to roadmapper (no blockers, no competing variants).
