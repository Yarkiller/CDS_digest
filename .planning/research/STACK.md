# Stack Research

**Domain:** Digest CDS — v1.3 (live SMTP mail, scheduled YouTube ingestion, backlog tech debt)
**Project:** Digest CDS (editorial knowledge service, СВА)
**Milestone:** v1.3 — subsequent milestone on a shipped app (v1 / v1.1 / v1.2 complete, 2026-10-14)
**Researched:** 2026-10-14
**Confidence:** HIGH (stack), MEDIUM (YouTube listing under ADR-0002)
**Scope:** NEW capabilities only. The v1/v1.1/v1.2 stack (FastAPI, React 19/React Router 7/Vite, self-hosted Supabase + pgvector, `data-collection`, `ingestion-service`, Typer, `youtube-transcript-api` 1.2.x, `openai` 3.x → DeepSeek, Playwright, pytest, uv workspace) is **already validated and not re-researched** — see `.planning/milestones/v1.1-*` and the superseded copy in git history of this file.

---

## Decision Summary (what v1.3 needs)

| # | Feature | Mechanism to add | New dependency? |
|---|---------|------------------|-----------------|
| 999.1 | Reader-route honesty for drafts | Reuse `MaterialReaderResponse` + `get_material_for_reader`; add an honest `status` field (or an admin draft route). No library. | **No** |
| 999.6 | Unsaved-changes guard | Implement `beforeunload` **and** migrate `web/src/App.jsx` from declarative `<BrowserRouter>` to a **data router** (`createBrowserRouter` + `RouterProvider`) so `useBlocker` is available. React Router 7.18.3 is already installed. | **No** (React Router ships `useBlocker`) |
| 999.7 | YAML merge keys (`<<`) | Fix `_StrictSafeLoader.construct_mapping` to skip the merge tag node and call `self.flatten_mapping(node)` first. PyYAML 6.0.3 already supports merges. | **No** |
| MAIL-02 | Signup confirmation mail | Configure **Supabase Auth (GoTrue) SMTP** container env (`GOTRUE_SMTP_*`, `GOTRUE_MAILER_AUTOCONFIRM=false`). This is ops/config, not Python code. | **No** (container env) |
| MAIL-01 | Live digest SMTP behind `Mailer` | Implement the existing `SmtpMailer` placeholder with **stdlib `smtplib` + `email.message.EmailMessage`**. | **No** (stdlib) |
| Sched | Scheduled ingestion on Linux VM | **systemd timer + `Type=oneshot` service** (`flock` safety net), driving the existing `ingest` CLI. | **No** (OS units) |

**Headline:** v1.3 needs **zero new runtime Python packages**. Every feature is either stdlib (`smtplib`, `email`, `xml`), already-installed (React Router, PyYAML), or OS/container config (systemd, GoTrue). The only *optional* new dependency is `defusedxml` **if** the RSS Atom parser is hardened (and to stop depending on it transitively).

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python `smtplib` + `email.message.EmailMessage` | stdlib (3.12) | SMTP transport + multipart HTML+text for MAIL-01 | The `Mailer` port is **synchronous** (`def send_digest`, `backend/src/backend/application/ports/mailer.py`) and is called from the synchronous `send_digest` use case. Stdlib SMTP is the only zero-dependency fit; `EmailMessage.set_content()` + `add_alternative(html, subtype="html")` produces a correct `multipart/alternative`. No abstraction needed for one relay. |
| Supabase Auth **GoTrue** SMTP config | GoTrue v2.196.0 (deployed) | MAIL-02 signup confirmation mail | On self-hosted Supabase, the confirmation mail is sent by the **Auth container**, not by app code. Root cause is already proven: `mailer_autoconfirm=false` + broken SMTP → HTTP 500 `Error sending confirmation email` and no user row (`.planning/debug/g-01-3b-signup-mailer.md`). Fix = configure `GOTRUE_SMTP_*` and turn autoconfirm off. |
| YouTube **Atom/RSS feed** (`youtube.com/feeds/videos.xml`) | no version | Enumerate a channel/playlist without an API key | No Google Cloud project, **no API key, no quota, no OAuth**. 15 most recent entries is ample for a weekly, idempotent scan. Fits ADR-0002 better than a Google Cloud API surface (single unauthenticated GET, no new credential). |
| Python `httpx` | `0.28.1` (already pinned in `data-collection`) | Fetch the Atom feed (and, if approved, YouTube Data API v3) | Already the external-HTTP standard in `data-collection` (`youtube_oembed.py`). Reuse the injected-client pattern (no `os.environ` in adapters, proxy only in composition). |
| **systemd timer + `Type=oneshot` service** | systemd (VM distro) | Scheduled ingestion | Structural one-instance-at-a-time (overlap guard), journald logging, `Persistent=true` catch-up, `OnFailure=`, `EnvironmentFile=`, cgroup sandboxing — all things cron makes you hand-roll. |
| Python `yaml` (PyYAML) | `6.0.3` (already pinned in `backend`) | Merge-key-aware strict pipeline config | 6.0.3 is the **current** release and already implements merge keys in `SafeConstructor.flatten_mapping`. No upgrade, no fork. |
| React Router `react-router-dom` | `7.18.3` (already installed) | 999.6 router guard | `useBlocker` is the sanctioned in-SPA navigation guard. Requires data-router mode (see 999.6 below). |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `defusedxml` | `0.7.1` (current) | Safe Atom XML parsing of the YouTube feed | **Only** if you parse the feed in Python. Make it an **explicit** `data-collection` dependency instead of relying on it transitively via `youtube-transcript-api`. Use `defusedxml.ElementTree.fromstring`. |
| `ssl` (stdlib) | — | TLS to the relay (`SMTP_SSL`/`STARTTLS`) + optional corporate CA bundle | MAIL-01; needed for a corporate relay with an internal CA. |
| `logging` / `journald` | stdlib | Delivery + scheduled-run logs | Adapter must log outcomes (never bodies/secrets) so the send path stays observable; systemd routes stdout/stderr to journald. |
| `flock` (util-linux) | OS | Second lock for the scheduled CLI | Only needed because the CLI can *also* be run by hand; the systemd unit already serializes the timer path. |

### Development / Ops Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| `systemd-analyze verify` | Validate unit files before enabling | Catches typos without a reboot. |
| `systemctl list-timers` / `journalctl -u digest-ingest` | Inspect schedule and run history | The whole reason to prefer systemd over cron. |
| `systemctl --failed` | Failure visibility | Pair with `OnFailure=` for a notification unit. |
| `uv` (workspace) | Add/remove deps, run the CLI | Existing rule: deps via `uv add --package <member>`. |
| Playwright + pytest | 999.1 / 999.6 behaviour + CLI unit tests | Mandatory TDD; no library change. |
| `openssl s_client -starttls smtp` | Verify the relay's TLS before writing adapter tests | Operator-side handshake check against the chosen relay. |

---

## (a) SMTP sending from Python

### Library and API shape

Use the **standard library**. No `aiosmtplib`, no `emails`, no `yagmail`, no `slimta`.

```python
# backend/src/backend/infrastructure/smtp_mailer.py  (replaces the SmtpMailer placeholder in stub_mailer.py)
import smtplib, ssl
from email.message import EmailMessage

def _build_message(*, sender: str, recipients: list[str], subject: str,
                   body_text: str, body_html: str | None) -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)      # or use BCC + explicit envelope — see below
    msg["Subject"] = subject
    msg.set_content(body_text)             # text/plain part
    if body_html:
        msg.add_alternative(body_html, subtype="html")  # → multipart/alternative
    return msg
```

Why stdlib fits *this* repo: the `Mailer` port is sync and already receives `body_text` + optional `body_html` (`backend/src/backend/application/ports/mailer.py`). `EmailMessage` maps 1:1 (`set_content`/`add_alternative` → the exact multipart HTML+text requirement). The adapter lives at `backend/src/backend/infrastructure/`, wired only in `backend/src/backend/composition/live.py` via `resolve_mailer(settings.mailer)`.

### Configuration when the relay is not yet chosen (operator-pluggable)

Add `SMTP_*` fields to `backend/src/backend/composition/settings.py` (mirroring the existing `from_env` dataclass pattern):

| Env var | Purpose | Default / notes |
|---------|---------|-----------------|
| `MAILER` | `stub` \| `smtp` | Keep `stub` default; **remove the fail-fast** in `resolve_mailer` and return `SmtpMailer` instead. |
| `SMTP_HOST`, `SMTP_PORT` | Relay endpoint | Required when `MAILER=smtp` → raise `ConfigurationError` at startup if blank (same fail-loud style as `build_supabase_service_client`). |
| `SMTP_SECURITY` | `starttls` \| `ssl` \| `none` | `starttls` for 587, `ssl` for 465. Make it explicit — do not auto-detect. |
| `SMTP_USER`, `SMTP_PASSWORD` | Credentials | Empty ⇒ anonymous/internal relay (skip `login()`); never logged. |
| `SMTP_FROM`, `SMTP_FROM_NAME` | Envelope/From | Must be on `@sberbank.ru` / `@omega.sbrf.ru` per ADR-0003. |
| `SMTP_CA_BUNDLE` | Corporate CA path | Optional; passed to `ssl.create_default_context(cafile=...)` for an internal CA. |
| `SMTP_TIMEOUT_SECONDS` | Connect + socket timeout | Default ~10s; bounded, never infinite. |

"Operator-pluggable" = **configuration, not code**: swapping the relay is an `.env` change plus `systemctl restart`. Keep the adapter free of relay-specific logic; no `os.environ` reads inside it (Settings injects a ready config dataclass — same rule as `data-collection` adapters, D-17).

TLS: `smtplib.SMTP_SSL(host, port, timeout=..., context=ctx)` for `ssl`; `smtplib.SMTP(host, port, timeout=...)` then `starttls(context=ctx)` then `login()` for `starttls`. Refuse `none` except for a same-host sink in tests.

### Multipart HTML + text

- `set_content(body_text)` → `text/plain; charset="utf-8"`.
- `add_alternative(body_html, subtype="html")` → wraps both in `multipart/alternative`, so plain-text clients get the honest text and HTML clients get the rendered digest.
- The use case already produces both (`render_email_html(...)` + `body_text` in `send_digest`), so **no changes to email composition** are needed for MAIL-01.
- Recipients: send one message per recipient (or use `Bcc` with an explicit envelope via `send_message(msg, to_addrs=[...])`) so the digest is never leaked between employees. Given the corporate audience, **prefer one connection, N messages** (`smtp.send_message(msg, from_addr=..., to_addrs=[addr])`) — leaks nothing, and the per-recipient accept/refuse result feeds `recipient_count` honestly.

### Honest delivery errors (mapping at the adapter boundary)

Map `smtplib`/socket failures into the repo's domain error taxonomy at the boundary — never let an SDK/OS exception leak upward:

| smtplib / socket exception | Meaning | Adapter behaviour |
|----------------------------|---------|-------------------|
| `smtplib.SMTPAuthenticationError` | Relay rejected credentials | **Permanent** → map to `PersistenceError`; no retry; log redacted reason. |
| `smtplib.SMTPConnectError`, `SMTPServerDisconnected` | Transient network/TLS | **Transient** → retry; then map to `PersistenceError`. |
| `smtplib.SMTPResponseException` (4xx `code`) | Transient server deferral | Retry. |
| `smtplib.SMTPResponseException` (5xx) | Permanent refusal | No retry → `PersistenceError`. |
| `smtplib.SMTPRecipientsRefused` | All/part of recipients refused | No retry; `.recipients` gives the per-address code. |
| `smtplib.SMTPException` (base), `OSError`, `ssl.SSLError`, `socket.timeout` | Catch-all transport failure | Retry transiently; then `PersistenceError`. |

`send_digest` already wraps the mail call in `except PersistenceError: logger.exception(...)` (CR-02 best-effort after publish), so mapping SMTP failures to `PersistenceError` plugs straight into the existing honesty path **without** re-publishing. Use `logger.exception`/redacted fields only — never log `body_text`, credentials, or full recipient lists (align with the CLI redaction rules, DBG-02).

**`recipient_count` honesty:** today `publication.recipient_count` comes from the RPC column `p_recipient_count int default 0` (migrations 005/006). For real delivery, return the mailer's actual accepted count from `SmtpMailer.send_digest` (`{"delivery_status": "sent"|"partial"|"failed", "recipient_count": <int>, "issue_url": ...}`) and surface that in `SendDigestResult` (or pass the real count into the claim+publish call). Do not keep echoing the hardcoded `0`.

### Retries / timeouts

`smtplib` has **no built-in retry** — implement a small bounded loop in the adapter:

- Retry only transient classes above; **3 attempts max**, exponential backoff with jitter (e.g. 1s, 4s), and a hard overall deadline (≈30–60s) so the HTTP request cannot hang.
- Set `timeout=` on the `SMTP`/`SMTP_SSL` constructor (connect + per-socket read).
- Since `send_digest` runs inside the FastAPI request (after the atomic publish), keep mail **time-boxed and best-effort** — a slow relay must not convert an already-published issue into a failed HTTP response.
- Consider a `Connection: close`/new connection per send; do **not** build a long-lived pooled SMTP session for a weekly job.

### MAIL-02 (signup confirmation) — same relay, different consumer

MAIL-02 is **not** a Python problem. Self-service `/register` calls Supabase JS `auth.signUp`, which hits GoTrue; GoTrue sends the confirmation mail itself. Configure on the VM's Supabase compose:

```
# supabase .env  →  forwarded into docker-compose auth service
SMTP_HOST=…            # GOTRUE_SMTP_HOST
SMTP_PORT=587
SMTP_USER=…
SMTP_PASS=…
SMTP_ADMIN_EMAIL=…     # GOTRUE_SMTP_ADMIN_EMAIL
SMTP_SENDER_NAME=…
ENABLE_EMAIL_AUTOCONFIRM=false   # GOTRUE_MAILER_AUTOCONFIRM
```

Verify end-to-end: `GET /auth/v1/settings` shows `mailer_autoconfirm:false`; `POST /auth/v1/signup` returns 2xx **and** the user row appears in Auth Users; the confirmation link resolves against `GOTRUE_SITE_URL` + `GOTRUE_MAILER_URLPATHS_CONFIRMATION`. Then update `docs/agents/local-platform-runbook.md` §4.1 (which currently documents autoconfirm as the Phase-1 unblock). **One relay serves both GoTrue and MAIL-01** — choose it once.

---

## (b) Enumerating a YouTube channel / playlist

### Recommended: public Atom/RSS feed (no API key)

```
https://www.youtube.com/feeds/videos.xml?channel_id=UCxxxxxxxxxxxxxxxxxxxxxx
https://www.youtube.com/feeds/videos.xml?playlist_id=PLxxxxxxxxxxxxxxxxxxxxxx
# long-form only (excludes Shorts):  playlist_id=UULFxxxxxxxxxxxxxxxxxxxxxx  (UC→UULF)
# all uploads, incl. Shorts:        playlist_id=UUxxxxxxxxxxxxxxxxxxxxxx    (UC→UU)
```

- **No API key, no OAuth, no Google Cloud project, no quota.** A single unauthenticated HTTPS GET.
- Returns the **15 most recent** entries (channel) / up to 15 (playlist). No pagination, so it is a *recent-window* source, not a backfill.
- For a **weekly** idempotent scan (the CLI already dedupes by unique `youtube_video_id` and returns `already_saved`), 15 entries/week is more than enough — the scheduler can run daily and still never miss a video.
- Fits ADR-0002 better than the Data API: no new credential to provision inside the contour, no external SaaS console dependency, one read-only GET that an egress proxy can allowlist.
- `@handle` URLs are **not** supported by the feed endpoint (HTTP 400) and resolving a handle→channel id requires scraping the channel page; require the **operator to supply `UC…` / `PL…` ids** in config (or resolve once, out of band).

### Alternative (only if >15 results / full history is required): YouTube Data API v3

Requires a **Google Cloud API key** (public data, no OAuth) and consumes the shared **10,000 units/day** quota:

| Call | Cost | Purpose |
|------|------|---------|
| `channels.list?part=contentDetails&id=UC…` | **1** | Read `contentDetails.relatedPlaylists.uploads` (or derive `UC…`→`UU…`). |
| `playlists.list?part=snippet,contentDetails&id=PL…` | **1** | Playlist metadata. |
| `playlistItems.list?playlistId=UU…&part=snippet,contentDetails&maxResults=50&pageToken=…` | **1 per page** | Enumerate items; follow `nextPageToken`. |
| `search.list?channelId=…` | **100** | ❌ Never — 100× the cost for the same videos. |

Over-quota → HTTP **403 `quotaExceeded`** (resets midnight PT). Listing a channel is `channels.list` (1) + `playlistItems.list` per page (1 each) — trivially inside 10k units/day. Use **plain `httpx`** with `params={"key": …}`; **do not** add `google-api-python-client`/`google-auth` (heavy discovery/OAuth machinery for two read endpoints). If adopted, it needs a **spike/ADR-0002 exception** before the scheduler phase can pass.

### Options that avoid an API key — the direct answer

| Option | API key? | Can list a channel/playlist? | Verdict |
|--------|----------|------------------------------|---------|
| **YouTube Atom feed** (`videos.xml`) | **No** | ✅ up to 15 recent | **Recommended** |
| YouTube oEmbed | **No** | ❌ only per-video metadata (needs a video URL) | Already used for metadata; cannot enumerate |
| Scraping the channel HTML page | No | ✅ but brittle + handle→id only | Avoid |
| `yt-dlp --flat-playlist -J` | **No** | ✅ full list | ❌ see below |
| YouTube Data API v3 | **Yes** | ✅ full, paginated | Fallback only, ADR-0002 exception |

### `yt-dlp` — explicitly not recommended for the scheduled path

- It is a **scraping tool with a fast-moving extractor** (release cadence ~monthly; treated 2026.03.03 as current): inside a frozen corporate VM it drifts out of date and silently breaks.
- Needs the **binary installed and kept current** (extra OS artifact outside `uv`, hard to pin, hard to audit) — a contour/security burden ADR-0002 does not want.
- Unauthenticated bulk metadata extraction from a datacenter IP is exactly what YouTube's bot checks target ("confirm you're not a bot"), so an unattended cron job is the worst possible caller.
- It can do far more than list (download media) — unnecessary capability for a listing-only need, and the project's content contract forbids media-as-material. Prefer the narrow feed.

### Integration point for listing

- Add a **new port** in `data-collection` (sibling of `VideoMetadataProvider`), e.g. `VideoListProvider.list_recent(source) -> tuple[VideoRef, ...]`, and an adapter `YouTubeFeedAdapter` (injected `httpx.AsyncClient`, mirroring `YouTubeOEmbedAdapter`, `data-collection/src/data_collection/adapters/youtube_oembed.py`).
- **Watch the frozen public API**: `data_collection.__all__` is a deliberately-locked seven-name surface (D-04/D-06). Adding a provider name is a public-API change → make it an explicit, test-visible decision (extend `__all__` + `tests/unit/test_data_collection_public_api.py`).
- New CLI surface in `ingestion-service/src/ingestion_service/cli.py`: keep `ingest <url>` as-is and add a scan command/option (e.g. `ingest --source channel|playlist --id UC…` or a `scan` command) that loops the existing `run_ingest_pipeline` per video. Compose the new provider in `ingestion_service/composition/clients.py` from `Settings` (add `YOUTUBE_CHANNEL_ID`/`YOUTUBE_PLAYLIST_ID`).
- Errors map to the existing `metadata` stage taxonomy (`data-collection/src/data_collection/errors/metadata.py`) so `--debug` stage lines stay 1:1.
- If you parse the feed in Python, add `defusedxml==0.7.1` explicitly and use `defusedxml.ElementTree.fromstring` (hardened against XML bombs; also drops the transitive-dependency reliance).

---

## (c) Scheduling on a Linux VM

### Recommended: systemd timer + `Type=oneshot` service

`cron` works, but for an unattended job holding secrets and hitting the network, systemd gives you the reliability properties for free:

| Need | cron | systemd timer |
|------|------|----------------|
| Overlap guard | none (runs two instances) | **structural** — `Type=oneshot` service is active until `ExecStart` exits |
| Missed run after downtime | skipped | `Persistent=true` fires **once** on next boot |
| Logging | `MAILTO`/hand-rolled redirect | journald (`journalctl -u`) |
| Failure hook | none | `OnFailure=` |
| Env/secrets | cron has a minimal env; you source files yourself | `EnvironmentFile=` (0600) |
| Jitter | none | `RandomizedDelaySec=` |
| Resource/sandbox control | none | cgroup + `ProtectSystem=`, `NoNewPrivileges=`, `PrivateTmp=` |

Skeleton:

```ini
# /etc/systemd/system/digest-ingest.service
[Unit]
Description=Digest CDS scheduled ingestion (drafts only)
After=network-online.target
Wants=network-online.target
OnFailure=digest-ingest-alert.service

[Service]
Type=oneshot
User=digestcds
WorkingDirectory=/opt/digest-cds
EnvironmentFile=/etc/digest-cds/ingest.env
ExecStart=/usr/bin/flock -n /run/digest-ingest.lock \
          /opt/digest-cds/.venv/bin/ingest --source playlist --id ${YOUTUBE_PLAYLIST_ID} --template lecture
TimeoutStartSec=3600
NoNewPrivileges=true
PrivateTmp=true
```

```ini
# /etc/systemd/system/digest-ingest.timer
[Unit]
Description=Run Digest CDS ingestion on a schedule
[Timer]
OnCalendar=*-*-* 06:00:00
Persistent=true
RandomizedDelaySec=15min
# AccuracySec=1min  (default) — optional tightening
[Install]
WantedBy=timers.target
```

Why each piece:

- **Locking:** `Type=oneshot` serializes the *timer* path; the `flock -n` wrapper is the belt-and-braces guard for the case where an operator *also* runs `ingest` by hand (the documented "half-migrated cron" race). `flock -n` exits non-zero instead of queuing, which is the honest behaviour for a bounded job.
- **Env handling:** `EnvironmentFile=` at 0600 root-owned, holding `DEEPSEEK_API_KEY`, `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, `YOUTUBE_PLAYLIST_ID` etc. Never put secrets in the unit file or world-readable files. systemd passes them to `Settings.from_env()` unchanged.
- **PATH/absolute paths:** systemd has a minimal PATH — invoke the **workspace venv's `ingest` entry point by absolute path** (`[project.scripts] ingest = "ingestion_service.cli:app"`). Do not rely on `uv` being on PATH at boot.
- **Logging:** stdout/stderr go to journald; `--debug` (stderr) is already secret-safe, so a debug run can be enabled temporarily via a drop-in without leaking. Set a `SystemMaxUse`/retention policy so the journal survives long enough to diagnose a weekly job.
- **Failure visibility:** `OnFailure=digest-ingest-alert.service` + `systemctl --failed` on the VM's health check; non-zero CLI exit (already the behaviour for `IngestError`/`ConfigurationError`) marks the unit failed. Optionally log `already_saved` counts so a "silent no-op" week is visible.
- **`Persistent=true` caveat:** it catches up **one** missed run, not every skipped interval — acceptable for a weekly scan (the feed only holds 15 entries anyway).
- **No auto-publish/auto-send:** the unit only writes drafts + shortlist rows; the mail/send path stays a separate admin action. Do not chain a send into this unit.
- **Idempotency (already shipped):** unique `youtube_video_id` + `already_saved` make re-runs safe; **lock it with a test** (per the milestone risk note) rather than adding scheduler-side dedupe state.
- **Timezone:** pin the server timezone (or write an explicit `OnCalendar` with a timezone) so `06:00` does not drift across DST.

### Alternatives

- **cron** — acceptable if the team standardises on it; then you must add `flock`, a log redirection, an env-sourcing wrapper, and your own failure alerting. Strictly more moving parts for the same job.
- **`systemd` user units** (`systemctl --user`) — viable if you want the job under a specific operator account, but then secrets live in the user's env; the system unit with a dedicated `User=` is cleaner.
- **In-process schedulers (APScheduler / Celery beat)** — out; there is no long-running ingestion service, and the project explicitly deferred pipeline execution.

---

## (d) PyYAML specifics for merge keys (`<<`)

No version change: **PyYAML 6.0.3** (current release, already pinned in `backend/pyproject.toml`) already supports merge keys.

### What is broken today

`_StrictSafeLoader.construct_mapping` (`backend/src/backend/infrastructure/yaml_pipeline_config_validator.py`) iterates the **raw** `node.value` and calls `self.construct_object(key_node, deep=deep)` to collect the "seen" keys. A `<<` entry's key node carries `tag:yaml.org,2002:merge`, for which `SafeConstructor` deliberately registers **no** constructor → `ConstructorError("could not determine a constructor for the tag 'tag:yaml.org,2002:merge'")`. So any document using `<<` is rejected. Merges never reach `flatten_mapping`, because the override never calls it before touching the node.

### Relevant PyYAML internals (verified against `/yaml/pyyaml`)

- `SafeConstructor.construct_mapping(node, deep=False)` **flattens merges first**, then delegates to `BaseConstructor.construct_mapping`.
- `SafeConstructor.flatten_mapping(node)` mutates the node **in place**: it removes `<<` pairs, recursively flattens nested merge sources, prepends the merged pairs (so explicit keys still win by coming later), deduplicates by key **value identity**, and re-tags `tag:yaml.org,2002:value` keys as `str`. It raises `ConstructorError` for `"expected a mapping for merging, but found %s"` / `"expected a mapping or list of mappings for merging, but found %s"`.
- The base `BaseConstructor.construct_mapping` silently last-wins on duplicate keys — which is exactly the leniency the repo's override replaces. **Keeping that rejection is the requirement (999.7).**
- The Composer preserves raw `tag:yaml.org,2002:merge` keys; merge handling is a *constructor* concern.
- `yaml.safe_load()` would return a plain `SafeLoader` result and **skip `_StrictSafeLoader`** — the repo correctly uses `yaml.load(text, Loader=_StrictSafeLoader)`; keep that call.

### Correct fix (accept merges, keep duplicate rejection)

```python
from yaml.nodes import MappingNode
from yaml.constructor import ConstructorError

_MERGE_TAG = "tag:yaml.org,2002:merge"

class _StrictSafeLoader(yaml.SafeLoader):
    def construct_mapping(self, node: MappingNode, deep: bool = False) -> dict[Any, Any]:
        if isinstance(node, MappingNode):
            # 1) Duplicate detection over EXPLICIT keys only — skip `<<` and the
            #    keys it injects, so a legitimate `<<: *base` + override is NOT a duplicate.
            seen: set[Any] = set()
            for key_node, _value_node in node.value:
                if key_node.tag == _MERGE_TAG:
                    continue
                key = self.construct_object(key_node, deep=deep)
                try:
                    hash(key)
                except TypeError:
                    continue
                if key in seen:
                    raise ConstructorError(
                        "while constructing a mapping",
                        node.start_mark,
                        f"found duplicate key ({key!r})",
                        key_node.start_mark,
                    )
                seen.add(key)
            # 2) Now expand merges in place (prepends merged defaults; explicit keys win).
            self.flatten_mapping(node)
        # SafeConstructor.construct_mapping flattens again (idempotent: no `<<` left) and builds the dict.
        return super().construct_mapping(node, deep=deep)
```

Ordering is the whole point: **duplicate-check the explicit entries first, then `flatten_mapping`**. Checking duplicates *after* flattening would wrongly reject `<<: *defaults` + `template: lecture` (the flattened list contains `template` twice — once injected, once explicit), which is *valid* YAML, not a duplicate. Because `flatten_mapping` mutates `node.value`, the explicit-key scan must run before it (or operate on a snapshot).

### Gotchas to cover in tests

- `<<: *anchor` (single mapping) and `<<: [*a, *b]` (list; earlier entries win) both accepted.
- Duplicate explicit keys still rejected → structured 400 `{"errors":[...]}` via the existing `MarkedYAMLError` catch in `validate()`.
- `<<:` pointing at a non-mapping → PyYAML's `ConstructorError` wording ("expected a mapping for merging, but found …") still maps to a structured reject.
- Nested merges (`flatten_mapping` recurses) and merge inside `roles: [...]`/nested maps.
- The 20 000-char cap, `RecursionError`→structured 400, and non-printable-char `ReaderError`→structured 400 paths are unchanged.
- Keep the strict loader class **module-private** in `infrastructure/` — no `yaml` import may reach `domain/` or `application/use_cases/` (architecture rule).

### What NOT to do for 999.7

- Do **not** switch to `ruamel.yaml` or a forked loader — PyYAML 6.0.3 already merges correctly; the bug is 6 lines in the override.
- Do **not** relax to `yaml.unsafe_load` or drop `_StrictSafeLoader` — that would weaken duplicate-key rejection, which 999.7 explicitly forbids.
- Do **not** hand-roll merge expansion in the validator — `flatten_mapping` already implements the spec (order, dedupe, nesting).

---

## Installation

```bash
# MAIL-01 / MAIL-02: no Python packages — stdlib smtplib + email; relay config is env + GoTrue container env.

# Scheduling: no packages — systemd units on the VM.

# Optional: harden YouTube feed parsing and stop relying on a transitive dep
uv add --package data-collection "defusedxml==0.7.1"

# 999.1 / 999.6 / 999.7: no new packages (React Router 7.18.3, PyYAML 6.0.3 already present)
uv sync
cd web && npm install   # only if package.json changed at all
```

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| stdlib `smtplib` + `EmailMessage` | `aiosmtplib` 5.1.3 | Only if a future mailer port is async — today the port and `send_digest` are sync; adopting async would ripple through the use case/route for no benefit. |
| stdlib `smtplib` | `emails` / `yagmail` / `slimta` | Never for one relay: extra dependency for templating/transport sugar the digest renderer already provides. |
| YouTube Atom feed (no key) | YouTube Data API v3 (key + quota) | Only when >15 recent items or full history is required — then buy it with a spike/ADR-0002 exception and plain `httpx`. |
| YouTube Atom feed | `yt-dlp --flat-playlist` | Only for a one-off manual audit on a developer workstation — never in the unattended path. |
| systemd timer | cron + `flock` | If the org's ops standard is cron-first and you accept hand-rolled logging/alerting/env. |
| `defusedxml` (explicit) | `feedparser` 6.0.14 | Only if many feed dialects (RSS 1.0/2.0/Atom/JSON) must be supported — overkill for one known YouTube Atom feed, and it pulls in extra parsing machinery. |
| React Router data router + `useBlocker` | Custom guard (context + `useNavigate` wrapper + `popstate`) | Only if migrating `App.jsx` to `createBrowserRouter` is judged too risky — accept more code and weaker coverage. |

---

## What NOT to Add

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `aiosmtplib`, async `Mailer` port | Port + `send_digest` are synchronous; async would force a cascade rewrite. | stdlib `smtplib`. |
| Celery / APScheduler / RQ / Prefect / Dagster / Airflow / Redis | PIPE execution is deferred past v1.3; a weekly CLI needs no broker. | systemd timer + `Type=oneshot`. |
| In-process schedulers (`schedule`, threads in FastAPI) | The backend is a reader; a scheduler inside it breaks the architecture and dies with the dyno/worker. | OS timer. |
| `google-api-python-client` / `google-auth` | Heavy discovery/OAuth stack for two read endpoints; adds a credential-management surface ADR-0002 dislikes. | YouTube Atom feed; if forced to the API, plain `httpx` + `?key=`. |
| `search.list` (YouTube) | 100 quota units/call vs 1 for `playlistItems.list`. | `channels.list` + `playlistItems.list` on the uploads playlist. |
| `yt-dlp` / `youtube-dl` in the scheduled path | Unmanaged binary, fast-decaying extractors, bot-check failures on datacenter IPs. | YouTube Atom feed. |
| `feedparser` | `sgmllib3k`-based, overkill for one known Atom feed. | `defusedxml.ElementTree`. |
| Storing/publishing raw media or transcript | Content contract (material = agent-prepared article only). | Existing captions→LLM→draft pipeline. |
| `ruamel.yaml`, PyYAML forks, `yaml.unsafe_load` | 6.0.3 already implements merges; relaxing the loader weakens duplicate rejection (999.7). | Fix `_StrictSafeLoader.construct_mapping`. |
| New SMTP abstraction/adapter registry | One relay, one port, one adapter. | `SmtpMailer` behind the existing `Mailer` port. |
| A second, scheduler-only dedupe store | The CLI is already idempotent on unique `youtube_video_id`. | `already_saved` + a locking test. |
| Auto-publish / auto-send from the timer | Explicit v1.3 non-goal. | Timer writes drafts only; admin sends. |
| `BeforeUnloadEvent` return-value reliance | Modern browsers ignore custom text and need `preventDefault()` + `returnValue`. | `useBlocker` + a correct `beforeunload` handler. |

---

## Version Compatibility

| Package / component | Version | Notes |
|---------------------|---------|-------|
| `pyyaml` | `6.0.3` (current) | No upgrade needed; merge support present via `flatten_mapping`. |
| `defusedxml` | `0.7.1` (current) | Pure-Python; currently transitive via `youtube-transcript-api` — promote to explicit if used. |
| `httpx` | `0.28.1` (pinned in `data-collection`) | Reuse the injected-client + `AsyncClient(timeout=…)` pattern; no new HTTP stack. |
| `react-router-dom` | `7.18.3` (installed) | `useBlocker` requires **data-router mode**; declarative `<BrowserRouter>` throws `useDataRouterContext("useBlocker")` is unavailable. Migration to `createBrowserRouter` + `RouterProvider` is the enabler. |
| `react` / `react-dom` | `19.2.8` (installed) | Compatible with the data-router migration; no version bump. |
| GoTrue (Supabase Auth) | v2.196.0 (deployed, per debug note) | `GOTRUE_SMTP_*` + `GOTRUE_MAILER_AUTOCONFIRM` supported; restart/recreate the auth container after env changes. |
| systemd | VM distro version | `Persistent=`, `RandomizedDelaySec=`, `OnFailure=`, `EnvironmentFile=` all long-stable. |
| `flock` | util-linux | Standard on the VM; `-n` for non-blocking exit. |
| Python | `>=3.12` (workspace) | `smtplib`, `email.message.EmailMessage`, `ssl`, `xml` all present. |

---

## Integration Map (repo)

```text
backend/
├── application/ports/mailer.py                       # unchanged port (sync, body_text + optional body_html)
├── application/use_cases/send_digest.py              # MAIL-01: surface mailer delivery_status/recipient_count
├── infrastructure/stub_mailer.py                     # replace SmtpMailer placeholder; resolve_mailer returns it
├── composition/settings.py                           # add SMTP_* from_env fields
├── composition/live.py                               # mailer=resolve_mailer(settings.mailer)  (no fail-fast)
├── infrastructure/yaml_pipeline_config_validator.py  # 999.7 merge-key fix (module-private loader)
└── interface/http/routes/
    ├── materials.py                                  # 999.1 honest draft handling (+ status field)
    └── admin.py                                      # send route unchanged contract

supabase-integration/
└── src/supabase_integration/profile_repository.py    # MAIL-01: add recipient/email listing (profiles = source of truth)

data-collection/
├── ports/…                                           # NEW VideoListProvider (public __all__ change — explicit decision)
└── adapters/youtube_feed.py                          # NEW httpx + defusedxml Atom adapter

ingestion-service/
├── cli.py                                            # NEW channel/playlist scan surface (keep `ingest <url>`)
├── composition/settings.py                           # YOUTUBE_CHANNEL_ID / YOUTUBE_PLAYLIST_ID
└── composition/clients.py                            # wire VideoListProvider from Settings

web/
└── src/App.jsx                                       # 999.6: <BrowserRouter> → createBrowserRouter + RouterProvider

ops/ (VM)
├── /etc/systemd/system/digest-ingest.{service,timer} # NEW
└── /etc/digest-cds/ingest.env (0600)                 # NEW — secrets, EnvironmentFile
```

---

## Confidence & Sources

| Area | Confidence | Basis |
|------|------------|-------|
| (a) SMTP via stdlib; errors/retries/timeouts | HIGH | Stdlib API; repo port is sync (`mailer.py`, `send_digest.py`); existing `ConfigurationError`/`PersistenceError` boundary conventions. |
| (a) MAIL-02 root cause + GoTrue SMTP env names | HIGH | `.planning/debug/g-01-3b-signup-mailer.md` (500 `Error sending confirmation email`, `mailer_autoconfirm=false`); Supabase self-hosting docs + `supabase/auth` `example.env` (`GOTRUE_SMTP_*`, `GOTRUE_MAILER_AUTOCONFIRM`). |
| (b) Data API v3 endpoints + quota units | HIGH | Google quota calculator: `channels.list`=1, `playlistItems.list`=1/page, `search.list`=100, default 10 000 units/day, 403 `quotaExceeded`; `playlistItems.list` docs. |
| (b) Atom feed endpoints, 15-entry limit, no key | HIGH | Multiple sources agree on `videos.xml?channel_id=|playlist_id=`, 15 most recent, no API key; `UULF`/`UU` variants. |
| (b) yt-dlp rejection | MEDIUM-HIGH | yt-dlp README (`--flat-playlist`, `-J`) + community guidance on bot checks/datacenter IPs; release cadence ~monthly. |
| (c) systemd vs cron | HIGH | `systemd.timer` man page (`Persistent=`, `RandomizedDelaySec=`) + operational comparisons; `flock -n` guidance. |
| (d) PyYAML merge internals | HIGH | Context7 `/yaml/pyyaml` (constructor reference: `flatten_mapping` semantics, `construct_mapping` order, merge-tag errors) + repo source. |
| 999.6 `useBlocker` requirement | HIGH | Context7 `/remix-run/react-router` (hook source: `useDataRouterContext`; docs: data router only) + `web/src/App.jsx` uses declarative `<BrowserRouter>`. |
| Versions (PyYAML 6.0.3, defusedxml 0.7.1, feedparser 6.0.14, aiosmtplib 5.1.3) | HIGH | PyPI JSON, fetched 2026-10-14. |

### Sources

- Context7 `/yaml/pyyaml` — `SafeConstructor.flatten_mapping`, `construct_mapping`, merge-tag errors, `safe_load` semantics.
- Context7 `/remix-run/react-router` — `useBlocker` (data-router requirement, `blocker.proceed()/reset()`), `createBrowserRouter`.
- Google for Developers — [Quota Calculator](https://developers.google.com/youtube/v3/determine_quota_cost), [playlistItems.list](https://developers.google.com/youtube/v3/docs/playlistItems/list).
- YouTube Atom feed behaviour — cors.dev guide, Feeder KB, Stack Overflow 29752447 (no API key; 15 entries).
- yt-dlp — [README](https://github.com/yt-dlp/yt-dlp), [metadata guide](https://ytdlp.org/guides/get-video-metadata).
- systemd — [systemd.timer(5)](https://freedesktop.org/software/systemd/man/latest/systemd.timer.html), ArchWiki Timers, cron-vs-systemd operational write-ups.
- Supabase — [Self-Hosting with Docker](https://supabase.com/docs/guides/self-hosting/docker), [Auth config](https://supabase.com/docs/guides/self-hosting/auth/config), `supabase/auth` `example.env`.
- PyPI JSON (2026-10-14) — `pyyaml==6.0.3`, `defusedxml==0.7.1`, `feedparser==6.0.14`, `aiosmtplib==5.1.3`.
- Repo — `backend/src/backend/application/ports/mailer.py`, `backend/src/backend/infrastructure/stub_mailer.py`, `backend/src/backend/composition/{settings,live}.py`, `backend/src/backend/application/use_cases/send_digest.py`, `backend/src/backend/infrastructure/yaml_pipeline_config_validator.py`, `data-collection/src/data_collection/adapters/youtube_oembed.py`, `ingestion-service/src/ingestion_service/{cli.py,composition/*}`, `supabase-integration/src/supabase_integration/profile_repository.py`, `web/src/App.jsx`, `web/package.json`, `.planning/debug/g-01-3b-signup-mailer.md`, `docs/agents/local-platform-runbook.md` §4.1, `docs/adr/0002-cloud-ru-foundrymodels-deployment.md`.

---

## Open Questions (need in-phase resolution, not stack blockers)

1. **Relay choice / ADR-0002 for YouTube listing** — pick the corporate SMTP relay (serves both GoTrue and MAIL-01) and decide Atom-feed-only vs Data API v3. Both are config/spike items, not stack questions, but the scheduler phase must not be planned before the source is settled.
2. **`recipient_count` plumbing** — whether the real count is passed into `claim_and_publish` (migrations 005/006 currently default `p_recipient_count=0`) or overridden on `SendDigestResult`.
3. **Recipient enumeration** — extend the existing `ProfileRepository` port or introduce a dedicated read-only directory port; both are one Supabase query over `profiles`.
4. **999.1 product shape** — relax `get_material_for_reader` to return drafts with an honest `status` (and a reader banner), or add a separate admin draft route; affects the frontend service call only.
5. **999.6 migration risk** — moving `App.jsx` to `createBrowserRouter` touches the whole route tree; scope it as its own plan with Playwright regression coverage.

---
*Stack research for: Digest CDS v1.3 — live mail, scheduled ingestion & backlog debt*
*Researched: 2026-10-14*
*Scope: NEW v1.3 capabilities only — the v1/v1.1/v1.2 stack is validated and not re-researched.*
