## Conflict Detection Report

### BLOCKERS (0)

(none)

### WARNINGS (0)

(none)

### INFO (3)

[INFO] Cross-ref cycle re-check passed (acyclic)
  Found: Classification cross_refs still list parent attributions (`acceptance_criteria` → `user_stories`, `error_handling` → `user_stories`)
  Note: Source docs mark those parents as non-edges («родительский документ; без обратной markdown-ссылки — acyclic ingest»). Directed ingest graph used for synthesis: user_stories → acceptance_criteria → error_handling (plus one-way edges to backlog_UI / SPECs / ADRs). No cycle among ingest docs. Depth cap 50 not exceeded.
  source: docs/digest-cds/user_stories.md; docs/digest-cds/acceptance_criteria.md; docs/digest-cds/error_handling.md

[INFO] Complementary PRD layers merged for US-01…US-31
  Found: Both PRDs cover the same story IDs — user_stories.md (persona/journey/Must-Should-Nice) and acceptance_criteria.md (Given/When/Then)
  Note: Not competing acceptance variants; synthesized as single REQ-US-* entries with description from user stories and acceptance from acceptance criteria. No WARNING bucket entry.
  source: docs/digest-cds/user_stories.md; docs/digest-cds/acceptance_criteria.md

[INFO] SPEC aligns with higher-precedence ADRs (no override needed)
  Found: technical_specification.md stack/NFR sections cite ADR-0001 (leaderboard post-v1), ADR-0002 (Cloud.ru + FoundryModels), ADR-0003 (email domains), ADR-0004 (self-hosted Supabase)
  Note: No SPEC assertion contradicted a higher-precedence ADR decision; ADR > SPEC precedence held without content rewrite. Locked ADR-0001 remains sole locked decision; no LOCKED-vs-LOCKED pair in ingest set.
  source: docs/digest-cds/technical_specification.md; docs/adr/0001-public-leaderboard-gamification.md; docs/adr/0002-cloud-ru-foundrymodels-deployment.md; docs/adr/0003-email-domain-restriction.md; docs/adr/0004-self-hosted-supabase-on-vm.md
