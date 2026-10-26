---
status: findings
files_reviewed: 11
counts:
  critical: 1
  warning: 3
  info: 4
  total: 8
reviewed_files:
  - ingestion-service/src/ingestion_service/diagnostics/__init__.py
  - ingestion-service/src/ingestion_service/diagnostics/redaction.py
  - ingestion-service/src/ingestion_service/application/ports/diagnostics.py
  - ingestion-service/src/ingestion_service/adapters/stderr_diagnostics.py
  - ingestion-service/src/ingestion_service/application/use_cases/ingest_pipeline.py
  - ingestion-service/src/ingestion_service/cli.py
  - ingestion-service/src/ingestion_service/tests_support/fakes.py
  - tests/unit/test_cli_debug_diagnostics.py
  - tests/unit/test_stderr_diagnostics.py
  - tests/unit/test_debug_redaction.py
  - tests/unit/test_ingest_pipeline.py
---

# Phase 15 Review — CLI `--debug` diagnostics

**Reviewed:** 2026-10-04
**Depth:** standard
**Scope:** the 11 files listed in `files_reviewed` against D-01…D-13 and the DBG-01/DBG-02 security goal.

## Summary

The phase is well-built: stdout/stderr separation is correct, the `StageDiagnostics`/`Clock`
ports keep the use-case infra-free, the allowlist + exact-value registry is the right primary
defense, and the default path stays byte-identical. All 32 tests in
`test_debug_redaction.py`, `test_stderr_diagnostics.py`, `test_cli_debug_diagnostics.py`, and
`test_ingest_pipeline.py` pass.

Two real defects sit in the redaction **safety net** (focus areas 1 and 4), and the exact-value
registry that the whole design leans on is never exercised end-to-end (focus area 5):

- **1 critical** — the denylist assignment regex cannot redact common underscore-named
  credentials (`secret_key=`, `access_token=`, `client_secret=`, …), so the DBG-02 safety net
  silently fails on exactly the names it is meant to catch.
- **3 warnings** — control-character stripping runs *after* the token patterns (a credential
  split by a control char leaks its tail); the registry wiring (`_settings_secrets`) has zero
  test coverage; and several tests assert field *presence* rather than value.
- **4 info** — line-format injection via unquoted values, duplicate sink construction, a
  line-level (not value-level) truncation cap, and a fragile identity check in `sanitize`.

No stdout-contamination path was found. Focus-area conclusions are recorded at the end.

---

## Critical

### C-1. Denylist cannot redact `secret_key=` / `access_token=` / `client_secret=` style credentials

**File:** `ingestion-service/src/ingestion_service/diagnostics/redaction.py:47-50`

```startLine:47:endLine:50:ingestion-service/src/ingestion_service/diagnostics/redaction.py
    re.compile(
        r"(?i)\b(?:api[_-]?key|secret|token|password|passwd|authorization|cookie)"
        r"\b\s*[=:]\s*\S+"
    ),
```

**Evidence (reproduced):**

```text
'access_token=abcdef123456'   -> 'access_token=abcdef123456'      # LEAK
'client_secret=abcdef123456'  -> 'client_secret=abcdef123456'     # LEAK
'secret_key=abcdef123456'     -> 'secret_key=abcdef123456'        # LEAK
'refresh_token=abcdef123456'  -> 'refresh_token=abcdef123456'     # LEAK
'private_key=abcdef123456'    -> 'private_key=abcdef123456'       # LEAK
'auth=abcdef123456'           -> 'auth=abcdef123456'              # LEAK
'api_key=abcdef123456'        -> '[redacted]'                     # ok
'token=abcdef123456'          -> '[redacted]'                     # ok
```

**Root cause:** `\b` is a word-boundary test and `_` is a word character, so
`\bsecret\b` / `\btoken\b` cannot match when the token name is prefixed or suffixed with
`_` (`client_secret`, `access_token`, `secret_key`). `api[_-]?key` is the only form that
special-cases an underscore, which masks the general gap. Boundaries are wrong here; a
lookbehind on a non-word character (or excluding `_`) is what is needed.

**Impact:** DBG-02 requires that proxy credentials, cookies, **and auth tokens** never be
printed, with the denylist as defense-in-depth behind the allowlist. `secret_key`/`access_token`
are the canonical env-var names for exactly those values, so the safety net fails on the most
likely shapes. `SUPABASE_SECRET_KEY` values are covered only by the exact-value registry; if
`_settings_secrets` misses a field (see W-2) or a secret arrives by another route, this is the
last line of defense and it does not hold. The existing test only proves `secret` *without* an
underscore, which is why the suite stays green.

**Recommendation:** match the key name preceded by a non-`[A-Za-z0-9_]` character and add the
common compound names, e.g.:

```python
re.compile(
    r"(?i)(?<![A-Za-z0-9_])(?:api[_-]?key|access[_-]?token|refresh[_-]?token|"
    r"client[_-]?secret|secret[_-]?key|secret|token|password|passwd|"
    r"authorization|cookie|private[_-]?key)\s*[=:]\s*\S+"
),
```

and add the negative cases (`secret_key=…`, `access_token=…`, `client_secret=…`) to
`test_debug_redaction.py`.

---

## Warning

### W-1. Control characters are stripped after the token patterns, so a split credential leaks its tail

**File:** `ingestion-service/src/ingestion_service/diagnostics/redaction.py:40-51, 68-81`

The control-character pattern is the **last** element of `DENY_PATTERNS`
(`redaction.py:51`) and `sanitize` applies the list in order (`redaction.py:74-80`). The token
patterns therefore run against text that still contains `\n`/`\x1b`, and their value classes
stop at the control character.

**Evidence (reproduced):**

```text
sanitize("Bearer abc\ndef_secondhalf") -> '[redacted]def_secondhalf'   # tail leaks
```

`Bearer abc` is masked, the `\n` is stripped, and `def_secondhalf` survives.

**Impact:** A credential containing (or preceded by) a control character is only partially
redacted. `test_control_characters_cannot_forge_extra_lines` only asserts the *line count*, so
the suite does not catch the partial-mask case. Threat model T-15-02 explicitly covers injected
control characters, so this is in scope.

**Recommendation:** strip `[\x00-\x1f\x7f]` **before** applying the denylist regexes (keep
`[redacted]` masking after), and add a regression test asserting a control-char-split token is
fully masked.

### W-2. The exact-value registry wiring (`_settings_secrets`) is never tested end-to-end

**Files:** `ingestion-service/src/ingestion_service/cli.py:51-60, 93-98`;
`tests/unit/test_cli_debug_diagnostics.py`

`_settings_secrets` seeds `SecretRegistry` from `deepseek_api_key`, `supabase_secret_key`, and
`youtube_proxy_url`, and is the primary defense for real secret values. Every CLI debug test
monkeypatches `build_ingest_deps` to a `SimpleNamespace` that has **no `settings` attribute**
(`test_cli_debug_diagnostics.py:_fake_deps`), so `getattr(deps, "settings", None)` is always
`None` and the registry is always empty. Grepping the suite for `_settings_secrets` /
`secrets=` finds no test.

**Impact:** A regression in `_settings_secrets` (wrong attribute name, dropping a field, the
`getattr` default) would leave D-08/DBG-02's strongest control silently empty and every test
would still pass.

**Recommendation:** add one CLI test where the fake `deps` carries a `settings` object whose
`deepseek_api_key` (say) equals the fake `video_id`; assert the captions debug line contains
`video_id=[redacted]` and the sentinel never appears in `result.stderr`. That proves
`Settings` → registry → `sanitize` → stderr.

### W-3. Several tests assert field presence rather than value/behavior

**Files:** `tests/unit/test_cli_debug_diagnostics.py:102-103, 162, 167-170, 204`;
`tests/unit/test_debug_redaction.py:32-35`

```startLine:167:endLine:170:tests/unit/test_cli_debug_diagnostics.py
    assert "material_id=" in persist_line
    assert "batch_id=" in persist_line
    assert "rank=" in persist_line
    assert "already_saved=" in persist_line
```

These pass even if a value is empty or printed as `None` (e.g. `rank=` with nothing after it),
and `test_deny_patterns_is_tuple_of_compiled_patterns` (`test_debug_redaction.py:32`) asserts
only the container shape, not redaction behavior. The `test_stderr_diagnostics.py` exact-line
test is the one place doing it right.

**Impact:** The presence-only assertions cannot detect a signal that is wired but whose value is
lost/`None`, and the shape test gives false confidence in the denylist (it is what let C-1
through).

**Recommendation:** assert concrete values where they are deterministic
(e.g. `"rank=1" in persist_line`, `"template=lecture"`), and replace the shape test with
behavioral deny-pattern coverage.

---

## Info

### I-1. `key=value` line format has no quoting, so an allowlisted string value can inject pseudo-fields

**File:** `ingestion-service/src/ingestion_service/adapters/stderr_diagnostics.py:89-95`

Values are interpolated verbatim (`f"{key}={value}"`). A value containing a space (the
`message` signal, or a `slug`/`language` that unexpectedly contains whitespace) renders as
extra fields on the same line — e.g. `message=foo reason=network_error exit_code=1`. Control
characters are stripped so new debug *lines* cannot be forged, but field ambiguity remains.

**Recommendation:** quote/escape string values, or restrict the format to scalar-safe keys.

### I-2. `StderrDiagnostics` is constructed twice in `cli.py`

**File:** `ingestion-service/src/ingestion_service/cli.py:85-98`

A no-secret sink is built before `build_ingest_deps()` (`:85`) and replaced with the
secret-seeded sink after (`:93-98`). The pre-build sink is intentional (config errors must emit
before `Settings` exists), but the duplication is easy to misread and means the config-error path
always runs with an empty registry.

**Recommendation:** extract a small factory (`_build_diagnostics(debug, settings=None)`) and
call it with `settings` after deps load, so the two behaviors are explicit.

### I-3. `MAX_VALUE_LENGTH` caps the whole assembled line, not each value

**File:** `ingestion-service/src/ingestion_service/diagnostics/redaction.py:81` (and `:36`)

`sanitize` returns `text[:MAX_VALUE_LENGTH]`, applied to the full `[HH:MM:SS] debug …` line. A
long `message` truncates mid-value and silently drops every trailing field
(`exit_code`, etc.). The constant name suggests a per-value cap.

**Recommendation:** cap each value before assembly (or document the line-level semantics
explicitly).

### I-4. `pattern is _CONTROL_CHARS` is fragile identity coupling inside `sanitize`

**File:** `ingestion-service/src/ingestion_service/diagnostics/redaction.py:74-80`

The masking loop branches on object identity against a module global. Reordering or copying the
pattern silently changes behavior to "mask control chars with `[redacted]`" instead of "strip".
A separate `CONTROL_CHAR_PATTERN` handled explicitly (or handled outside the tuple — see W-1)
would be clearer.

---

## Focus-area conclusions

1. **Redaction bypasses / secret leakage** — C-1 and W-1 are genuine bypasses in the denylist
   net; the allowlist primary path holds. The exact-value registry is correct in isolation
   (`test_secret_registry_masks_exact_value`) but is untested at the CLI wiring level (W-2).
2. **stdout contamination** — none found. `_emit_debug` (`cli.py:67-69`) is the only debug sink
   and always uses `typer.echo(..., err=True)`; `NullDiagnostics` guarantees zero output when
   `--debug` is off; the default-path tests assert `result.stderr == ""` and the frozen stdout
   lines. Verified passing.
3. **Injected-emitter deviation** — the deviation is correct and justified. The adapter stays
   framework-free (no `typer` import, matching `test_ingestion_service_has_no_typer_import`),
   `cli.py` injects `typer.echo(..., err=True)`, and the `sys.stderr` fallback plus the
   `stream`/`emit` precedence are coherent. No new stdout path was introduced.
4. **Redaction regex correctness** — `Bearer` (and its ordering before the assignment pattern),
   `sk-`, JWT, and URL-userinfo patterns behave as intended. The assignment pattern is broken
   for underscore-suffixed/compound names (C-1), and pattern/control-char ordering is wrong
   (W-1). JWT pattern ignores 5-segment (JWE) tokens and `=`-padded segments — acceptable for
   now, worth a comment.
5. **Presence-vs-behavior tests** — W-3; the most consequential gap is the missing
   underscore-credential negative cases that would have caught C-1, plus the untested registry
   wiring (W-2).

## Verification performed

- `uv run pytest tests/unit/test_debug_redaction.py tests/unit/test_stderr_diagnostics.py tests/unit/test_cli_debug_diagnostics.py tests/unit/test_ingest_pipeline.py -q` → **32 passed**.
- Ad-hoc probes of `sanitize` / `SecretRegistry` confirming the C-1 and W-1 reproductions above.
