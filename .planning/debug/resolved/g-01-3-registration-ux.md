---
status: resolved
resolved:
  at: 2026-10-13
  evidence: "Self-service /register with Login nickname and slim email+password login shipped; Playwright contracts added (v1 Phase 1)"
trigger: "Diagnose UAT gap G-01-3 for Digest CDS Phase 1. Do NOT implement fixes — diagnose only. Symptoms: (1) Регистрация inactive / does not lead to registration (2) Login must NOT have Name field (3) Registration SHOULD have name field (ФИО/Имя)."
created: 2026-09-19T19:11:00Z
updated: 2026-09-19T19:15:00Z
goal: find_root_cause_only
symptoms_prefilled: true
gap_id: G-01-3
audit_acknowledged:
  milestone: v1
  at: 2026-09-22
  status: diagnosed
---

## Current Focus

hypothesis: "G-01-3 is a Phase-1 product/UX mismatch: LoginPage embeds display-name on login and links «Регистрация» to /login, while signUp was explicitly OPT-OUT under D-08 — so registration never existed as a separate screen."
bug_class: Bohrbug
test: "Read LoginPage Link target, App routes, authApi exports, COVERAGE signUp row, D-08"
expecting: "No /register route; Link to=/login; no signUp; name field on login; COVERAGE OPT-OUT confirmed"
next_action: "Return ROOT CAUSE FOUND to orchestrator (diagnose-only)"
known_pattern_candidate: none (no knowledge-base.md)

reasoning_checkpoint:
  hypothesis: "Dead registration CTA + name-on-login exist because Phase 1 shipped a single LoginPage that conflates login with optional post-login display-name update, while self-service signUp was scoped out (D-08 / COVERAGE OPT-OUT)."
  confirming_evidence:

    - "LoginPage.jsx L192-194: Link to=\"/login\" labeled Регистрация"
    - "App.jsx: only /login auth route; no RegisterPage file"
    - "authApi.js: signInWithPassword + updateAuthDisplayName; no signUp export"
    - "COVERAGE.md: signUp OPT-OUT — users seeded in Auth dashboard (D-08)"
    - "tests/auth.spec.js fills Имя on login path — locks in wrong UX"
  falsification_test: "Finding a working /register route with signUp and name-only-on-register would refute this"
  fix_rationale: "N/A — diagnose only; fix requires scope decision (remove CTA vs implement register)"
  blind_spots: "Whether product owner intends to reverse OPT-OUT for Phase 1 or keep D-08 and only fix UX copy/CTA"
  candidate_causes:

    - "code: LoginPage wrong Link + name field on login; missing RegisterPage/route/signUp"
    - "config/scope: Phase 1 D-08 + COVERAGE deliberately OPT-OUT signUp"
  and_gate: "yes — wrong UI (code) AND intentional no-signUp scope (config) together produce the UAT failure: CTA promises registration that Phase 1 forbade"

## Symptoms

expected: Corporate login works; login UX is email+password only; registration is a separate form with a clear name field (ФИО or Имя); «Регистрация» leads to that form.
actual: «Регистрация» does not lead to registration; login form has Имя field that must be filled on login; no separate registration form with name.
errors: none (UX/product gap, not runtime exception)
reproduction: Open /login; observe Имя field; click «Регистрация» — stays on same login route; no /register page.
started: Observed during Phase 1 UAT test 3 (G-01-3); present in current LoginPage implementation.

## Eliminated

- hypothesis: "Регистрация button is CSS-disabled / inactive (pointer-events none)"
  evidence: "Link is a real react-router Link with underline class; not disabled — it navigates to the same /login path (no-op route change)."
  timestamp: 2026-09-19T19:12:00Z

- hypothesis: "signUp exists in authApi but UI fails to call it"
  evidence: "authApi.js has no signUp function; only signIn, signOut, getSession, updateAuthDisplayName."
  timestamp: 2026-09-19T19:13:00Z

## Evidence

- timestamp: 2026-09-19T19:12:00Z
  checked: web/src/pages/LoginPage.jsx
  found: "Имя field (id=display-name) on login form L101-118; after signIn optionally updateDisplayName + updateAuthDisplayName L52-56; footer Link to=\"/login\" for Регистрация L192-194"
  implication: "Name collected at login; registration CTA is a same-route dead end"

- timestamp: 2026-09-19T19:12:30Z
  checked: web/src/App.jsx
  found: "Only Route path=/login for LoginPage; no /register"
  implication: "No registration screen wired"

- timestamp: 2026-09-19T19:13:00Z
  checked: web/src/services/authApi.js
  found: "signInWithPassword path only; updateAuthDisplayName via updateUser; no signUp"
  implication: "Self-service registration API surface absent by design of this module"

- timestamp: 2026-09-19T19:13:30Z
  checked: .planning/phases/01-platform-foundation-auth/COVERAGE.md + 01-CONTEXT.md D-08
  found: "signUp OPT-OUT — users seeded in Auth dashboard (D-08); D-08 = manual 1–2 corporate test users"
  implication: "Phase 1 planning explicitly excluded self-service registration"

- timestamp: 2026-09-19T19:14:00Z
  checked: .planning/REQUIREMENTS.md AUTH-01..03; acceptance US-01/US-02; 01-UAT G-01-3
  found: "AUTH/US stories cover sign-in only; UAT truth now requires separate registration form with name — conflicts with OPT-OUT"
  implication: "UAT gap is product expectation vs Phase 1 scoped delivery plus partial wrong UI"

- timestamp: 2026-09-19T19:14:30Z
  checked: tests/auth.spec.js
  found: "test 'shows entered display name in header after login' fills getByLabel /^имя$/i on /login"
  implication: "Automated suite encodes name-on-login as intended behavior — would need rewrite if UX corrected"

- timestamp: 2026-09-19T19:14:45Z
  checked: Glob Register*.jsx; Grep Регистрация under web/
  found: "Zero Register pages; sole Регистрация string is the dead Link on LoginPage"
  implication: "Missing artifacts confirmed"

## Resolution

root_cause: "Phase 1 never implemented self-service registration (D-08 + COVERAGE signUp OPT-OUT), but LoginPage still shows a «Регистрация» link to /login and incorrectly places the display-name field on the login form (post-login profile/Auth metadata update). UAT G-01-3 therefore fails on three coupled UX defects plus a scope conflict with product language that expects a real registration form."
fix: ""
verification: ""
files_changed: []
oracle_type: specified
specialist_hint: react
