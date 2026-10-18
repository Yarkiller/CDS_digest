---
phase: "21"
slug: "mail-01-live-smtp-digest-delivery"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-16"
---

# Phase 21 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 (`uv run pytest`) |
| **Config file** | `pyproject.toml` → `[tool.pytest.ini_options]` (`testpaths = ["tests/unit"]`) |
| **Quick run command** | `uv run pytest tests/unit/test_send_digest.py tests/unit/test_stub_mailer.py -q` |
| **Full suite command** | `uv run pytest tests/unit -q` |
| **Estimated runtime** | ~30–90 seconds (unit suite) |

---

## Sampling Rate

- **After every task commit:** Run focused `uv run pytest … -x` for touched files
- **After every plan wave:** Run `uv run pytest tests/unit -q`
- **Before `/gsd-verify-work`:** Full unit suite must be green
- **Max feedback latency:** 90 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 21-W0 | 01 | 0 | MAIL-01..05 | — | N/A | unit stubs | Wave 0 files listed below | ❌ W0 | ⬜ pending |
| 21-01 | 01 | 1 | MAIL-03 | T-21-03 | Recipients via service_role only | unit | `uv run pytest tests/unit/test_send_digest.py -k "recipient or stub_message or empty_audience" -x` | ❌ W0 | ⬜ pending |
| 21-02 | 01 | 1 | MAIL-01 / D-88 | T-21-01 | Mail fail after publish → success | unit | `uv run pytest tests/unit/test_send_digest.py::test_send_mail_failure_after_publish_still_returns_success -x` | ❌ W0 | ⬜ pending |
| 21-03 | 02 | 2 | MAIL-04 | T-21-02 | SMTP errors → MailDeliveryError | unit | `uv run pytest tests/unit/test_smtp_mailer.py -x` | ❌ W0 | ⬜ pending |
| 21-04 | 02 | 2 | MAIL-04 / D-08 | T-21-04 | Consecutive failure stop | unit | `uv run pytest tests/unit/test_smtp_mailer.py -k consecutive -x` | ❌ W0 | ⬜ pending |
| 21-05 | 02 | 2 | MAIL-05 / D-16 | T-21-05 | Incomplete SMTP_* fail-fast | unit | `uv run pytest tests/unit/test_stub_mailer.py tests/unit/test_live_container_wiring.py -x` | ✅ amend | ⬜ pending |
| 21-06 | 03 | 3 | MAIL-03 | — | `delivered_count` on HTTP/SPA | unit | `uv run pytest tests/unit/test_http_admin.py -k send -x` | ✅ amend | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_smtp_mailer.py` — MAIL-04 / D-05 / D-08 / TLS branches
- [ ] `tests/unit/test_send_digest.py` — amend stubbed/message; add mail-failure, audience M, delivered_count, ping honesty
- [ ] `tests/unit/test_profile_repository_recipients.py` (or extend existing) — list + exclude empty/malformed
- [ ] `backend/tests_support/in_memory.py` — `list_digest_recipients`; publisher `recipient_count=`
- [ ] Amend `test_stub_mailer.py` — `ConfigurationError` + complete SMTP_* resolve
- [ ] Amend `test_live_container_wiring.py` / `test_composition_container.py`
- [ ] Amend `web/src/services/adminApi.js` mock for `delivered_count` + stub message
- [ ] Framework install: already present via `uv` — no new install

*Existing infrastructure covers the framework; Wave 0 is test stubs/amends only.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live corporate relay smoke with `MAILER=smtp` | MAIL-01 | Ops flip; not a merge blocker (D-15) | Follow `docs/agents/local-platform-runbook.md` SMTP smoke/rollback after code lands |

*All in-repo behaviors have automated verification; live relay is ops-only.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 90s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
