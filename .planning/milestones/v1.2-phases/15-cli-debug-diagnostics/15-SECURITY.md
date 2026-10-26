---
phase: 15
slug: cli-debug-diagnostics
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: 2026-10-04
---

# Phase 15 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Process CLIs → operator terminal | The `--debug` side-channel writes diagnostics to stderr while stdout stays the machine contract | Debug lines: stage names, ids/counts/enums, static messages (low–medium sensitivity) |
| Ingestion runtime config → debug sink | Runtime `Settings` secrets are registered with the sink so exact values cannot be echoed | API keys / secret keys / proxy URL credentials (high sensitivity) |
| Use-case → diagnostics port | `run_ingest_pipeline` talks to a `StageDiagnostics` Protocol only; no infra imports | Stage events and observable DTO fields (low sensitivity) |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-15-01 | Information Disclosure | `redaction.py` / `stderr_diagnostics.py` / `cli.py` | high | mitigate | Allowlist `ALLOWED_KEYS` + exact-value `SecretRegistry` wired via `_settings_secrets`→`StderrDiagnostics(secrets=)`; `sanitize` at the single sink chokepoint | closed |
| T-15-02 | Tampering | `redaction.py` | medium | mitigate | `_CONTROL_CHARS.sub` strips control characters so they cannot forge extra lines | closed |
| T-15-03 | Information Disclosure | `stderr_diagnostics.py` / `cli.py` | medium | mitigate | Sink emits only via `err=True` echo / injected stream / `sys.stderr`; stdout frozen by contract tests | closed |
| T-15-04 | Information Disclosure | `ingest_pipeline.py` / `stderr_diagnostics.py` | high | mitigate | Metadata line emits `video_id` only; failure line emits `reason`/`exit_code` only | closed |
| T-15-05 | Tampering | `redaction.py` / use-case guards | medium | mitigate | `sanitize` never raises (mask-not-fail); emission guarded by `if diagnostics is not None`; exit codes/envelope frozen | closed |
| T-15-06 | Information Disclosure | `stderr_diagnostics.py` `config_error` | medium | mitigate | `stage=config` routes through `_emit`→`sanitize`; all config messages are static and non-secret | closed |
| T-15-07 | Information Disclosure | `redaction.py` assignment denylist | high | mitigate | Non-word left boundary `(?<![A-Za-z0-9_])` + compound alternatives, no trailing `\b`; underscore-compound credentials mask to `[redacted]` | closed |
| T-15-08 | Tampering | `redaction.py` token ordering | medium | mitigate | Control-char strip applied before the token loop; no partial-mask tail leak | closed |
| T-15-09 | Information Disclosure | `redaction.py` value-tail / header-scheme patterns | medium | mitigate | **open — below high threshold (non-blocking)**: denylist masks the first token of a header/scheme value, leaving a tail (e.g. `Authorization: Basic <b64>`). Not reachable in-scope — every emitted value is a constrained id/count/enum/static message; primary control (`SecretRegistry`) intact | open — below high threshold (non-blocking) |
| T-15-10 | Denial of Service | `redaction.py` URL-userinfo pattern | low | mitigate | **open — below high threshold (non-blocking)**: URL-userinfo regex is quadratic on long unbroken runs; not reachable in-scope (emitted values are small). Hardening: bound/replace with a linear-time pattern | open — below high threshold (non-blocking) |
| T-15-11 | Information Disclosure | `ingest_pipeline.py` | high | mitigate | Only `transcript_chars`/`transcript_words`/`response_chars` emitted; bodies never passed to the sink | closed |
| T-15-12 | Elevation of Privilege | `cli.py` / `stderr_diagnostics.py` | medium | mitigate | No env read enables debug; only the `typer.Option("--debug")` branch builds a live sink | closed |
| T-15-SC | Tampering | dependencies | high | mitigate | No dependency/`uv.lock` changes; new modules import stdlib only | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-15-01 | T-15-09 | Denylist value-tail leak is unreachable in Phase 15: emitted signal values are constrained ids/counts/enums/static messages; the exact-value `SecretRegistry` remains the primary control. Scheduled as non-blocking hardening (anchor value capture to the credential token). | orchestrator (verify-work) | 2026-10-04 |
| AR-15-02 | T-15-10 | Quadratic `sanitize` on a 10⁵⁺-char unbroken run is unreachable in Phase 15: `sanitize` only ever receives assembled debug lines with small values. Scheduled as non-blocking hardening (linear-time URL-userinfo pattern). | orchestrator (verify-work) | 2026-10-04 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-04 | 13 | 11 | 2 (non-blocking) | gsd-security-auditor (retroactive-STRIDE, ASVS L1, block_on high) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-04
