# Phase 9 Pattern Mapping

*Source: `09-CONTEXT.md`, `09-RESEARCH.md`*  
*Goal: map every file Phase 9 will touch to a concrete existing analog so the planner can reuse known shapes.*

---

## 1. Phase 8 contract amendments (data-collection)

These files are modified because `ArticleDraft` must grow `roles`, which then flows through assembler into `MaterialDraft`.

| # | File | Role | Data flow | Closest analog |
|---|------|------|-----------|----------------|
| 1 | `data-collection/src/data_collection/dto/article_draft.py` | LLM output DTO | DeepSeek adapter → assembler | Current `ArticleDraft` (title/dek/body) |
| 2 | `data-collection/src/data_collection/dto/material_draft.py` | Persist input DTO | assembler → persist port | Current `MaterialDraft` provenance fields |
| 3 | `data-collection/src/data_collection/assemble.py` | Pure assembler | `ArticleDraft + VideoMetadata + label → MaterialDraft` | Current `assemble_material_draft` |
| 4 | `data-collection/src/data_collection/templates/lecture.md` | Prompt template | instructs LLM to emit audience roles | Current lecture template |
| 5 | `data-collection/src/data_collection/templates/podcast.md` | Prompt template | instructs LLM to emit audience roles | Current podcast template |
| 6 | `data-collection/src/data_collection/adapters/deepseek_article.py` | Adapter validation | JSON → validated `ArticleDraft` with roles fallback | Current `process()` + `ArticleDraft.model_validate` |
| 7 | `data-collection/src/data_collection/tests_support/fakes.py` | Test doubles | New `FakeDraftPersister` will live in ingestion-service, but fake style mirrors existing fakes | `FakeTranscriptProvider`, `FakeArticleGenerator` |

### 1.1 Existing `ArticleDraft` shape

```startLine:1:endLine:22:C:/Users/Yarkiller/PycharmPET-Projects/Digital_CDS/data-collection/src/data_collection/dto/article_draft.py
"""Internal ArticleDraft — LLM output only; not public package API (D-06)."""

from pydantic import BaseModel, Field, field_validator

from data_collection.dto._validators import strip_non_blank


class ArticleDraft(BaseModel):
    title: str = Field(min_length=1)
    dek: str = Field(min_length=1)
    body_markdown: str = Field(min_length=1)

    @field_validator("title", "dek", "body_markdown")
    @classmethod
    def _strip_non_blank(cls, value: str) -> str:
        return strip_non_blank(value)
```

**Mapping:** add `roles: list[RoleKind]` with `RoleKind = Literal["employee", "analyst", "ds"]` and a validator that filters unknown values.

### 1.2 Existing `MaterialDraft` shape

```startLine:1:endLine:36:C:/Users/Yarkiller/PycharmPET-Projects/Digital_CDS/data-collection/src/data_collection/dto/material_draft.py
"""MaterialDraft DTO — prepared article + provenance for draft persist (D-05, D-13)."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from data_collection.dto._validators import strip_non_blank


class MaterialDraft(BaseModel):
    title: str = Field(min_length=1)
    dek: str = Field(min_length=1)
    body_markdown: str = Field(min_length=1)
    source_url: str = Field(min_length=1)
    youtube_video_id: str = Field(min_length=1)
    source_author: str = Field(min_length=1)
    provenance_label: str = Field(min_length=1)
    source_published_at: datetime | None = None

    @field_validator(
        "title",
        "dek",
        "body_markdown",
        "source_url",
        "youtube_video_id",
        "source_author",
        "provenance_label",
    )
    @classmethod
    def _strip_non_blank(cls, value: str) -> str:
        return strip_non_blank(value)

    @field_validator("source_published_at")
    @classmethod
    def _require_aware(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("source_published_at must be timezone-aware")
        return value
```

**Mapping:** add `roles: list[RoleKind]` after `source_published_at`; reuse the same validator pattern.

### 1.3 Existing assembler

```startLine:1:endLine:30:C:/Users/Yarkiller/PycharmPET-Projects/Digital_CDS/data-collection/src/data_collection/assemble.py
"""Pure assembler: ArticleDraft + VideoMetadata + provenance_label → MaterialDraft."""

from __future__ import annotations

from data_collection.dto.article_draft import ArticleDraft
from data_collection.dto.material_draft import MaterialDraft
from data_collection.dto.video_metadata import VideoMetadata


def assemble_material_draft(
    article: ArticleDraft,
    metadata: VideoMetadata,
    provenance_label: str,
) -> MaterialDraft:
    return MaterialDraft(
        title=article.title,
        dek=article.dek,
        body_markdown=article.body_markdown,
        source_url=metadata.source_url,
        youtube_video_id=metadata.video_id,
        source_author=metadata.author,
        provenance_label=provenance_label,
        source_published_at=metadata.published_at,
    )


def require_material_draft(value: object) -> MaterialDraft:
    if not isinstance(value, MaterialDraft):
        raise TypeError("MaterialDraft required")
    return value
```

**Mapping:** add `roles=article.roles` to the constructor.

### 1.4 Existing template style

```startLine:1:endLine:12:C:/Users/Yarkiller/PycharmPET-Projects/Digital_CDS/data-collection/src/data_collection/templates/lecture.md
## Тезис

Summarize the core thesis of the transcript in one clear sentence.

## Ход рассуждения

Reconstruct the main argument, evidence, and reasoning from the transcript.
Do not invent facts, names, or numbers that are not in the transcript.

## Вывод

State the key takeaway for a СВА reader.
```

**Mapping:** append a section such as:

```markdown
## Аудитория

Кто целевая аудитория материала? Верни список ролей из: employee, analyst, ds.
```

### 1.5 Existing DeepSeek adapter validation point

```startLine:140:endLine:170:C:/Users/Yarkiller/PycharmPET-Projects/Digital_CDS/data-collection/src/data_collection/adapters/deepseek_article.py
        try:
            return ArticleDraft.model_validate(payload)
        except ValidationError as exc:
            raise ArticleInvalidDraft(
                transcript.video_id,
                exception_class=_exception_class(exc),
            ) from exc
```

**Mapping:** after `model_validate`, normalize `roles`: filter to valid `RoleKind`; if empty, fallback to `["employee"]`.

---

## 2. Phase 9 persist artifacts (ingestion-service)

### 2.1 Port + result DTO

| # | File | Role | Data flow | Closest analog |
|---|------|------|-----------|----------------|
| 8 | `ingestion-service/src/ingestion_service/application/ports/persist.py` | Application port | use-case → adapter | `data_collection.ports.article_generator.ArticleGenerator` |
| 9 | `ingestion-service/src/ingestion_service/adapters/supabase_persist.py` | Supabase RPC adapter | port → Supabase `.rpc(...)` | `SupabaseMaterialRepository.save` + `SupabaseShortlistRepository.get_current_batch` |
| 10 | `ingestion-service/src/ingestion_service/adapters/persist_errors.py` | Module-local errors | adapter → mapper | `data_collection.errors.article.ArticleError` |
| 11 | `ingestion-service/src/ingestion_service/mapping/persist.py` | Error mapper | `DraftPersistError → IngestError(stage="persist")` | `ingestion_service.mapping.captions` / `metadata` / `article` |
| 12 | `ingestion-service/src/ingestion_service/application/use_cases/persist_draft.py` | Use-case | generates slug/reading_minutes/roles, calls port | Pure function like `assemble_material_draft` |
| 13 | `ingestion-service/src/ingestion_service/composition/clients.py` | Client factories | builds service-role client + persister | `build_deepseek_article_generator` |
| 14 | `ingestion-service/src/ingestion_service/composition/settings.py` | Env settings | loads `SUPABASE_*`, `SHORTLIST_BATCH_SIZE` | Existing `Settings` |
| 15 | `ingestion-service/pyproject.toml` | Dependency manifest | adds `supabase` (+ optional `python-slugify`) | Current `data-collection` / `ingestion-service` deps |
| 16 | `ingestion-service/.env.example` | Env template | documents new variables | Root `.env.example` (tested by `test_env_example.py`) |

### 2.2 Existing port pattern

```startLine:1:endLine:10:C:/Users/Yarkiller/PycharmPET-Projects/Digital_CDS/data-collection/src/data_collection/ports/article_generator.py
"""ArticleGenerator port — LLM prepares ArticleDraft from Transcript (D-16)."""

from __future__ import annotations

from typing import Protocol

from data_collection.dto.article_draft import ArticleDraft
from data_collection.dto.template_kind import TemplateKind
from data_collection.dto.transcript import Transcript


class ArticleGenerator(Protocol):
    async def process(
        self, transcript: Transcript, template: TemplateKind
    ) -> ArticleDraft: ...
```

**Mapping for new port:**

```python
from dataclasses import dataclass
from typing import Protocol

from data_collection.dto.material_draft import MaterialDraft


@dataclass(frozen=True)
class PersistResult:
    material_id: int
    slug: str
    batch_id: int
    rank: int


class PersistPort(Protocol):
    def persist(self, material_draft: MaterialDraft) -> PersistResult: ...
```

### 2.3 Existing adapter-local error pattern

```startLine:1:endLine:50:C:/Users/Yarkiller/PycharmPET-Projects/Digital_CDS/data-collection/src/data_collection/errors/article.py
"""Article adapter errors — module-local taxonomy only (D-13)."""

from __future__ import annotations

from typing import Any


class ArticleError(Exception):
    """Base article-generation failure at the adapter boundary."""

    def __init__(self, video_id: str, **context: Any) -> None:
        self.video_id = video_id
        self.context = context
        for key, value in context.items():
            setattr(self, key, value)
        super().__init__(f"article error for {video_id}")


class ArticleNetworkError(ArticleError):
    """Timeout, DNS, or connection failure before a DeepSeek response."""
```

**Mapping for new adapter errors:**

```python
class DraftPersistError(Exception):
    def __init__(self, reason: str, *, video_id: str | None = None, context: dict | None = None) -> None:
        self.reason = reason
        self.video_id = video_id
        self.context = context or {}
        super().__init__(f"persist {reason}")

class DraftPersistConflictError(DraftPersistError): ...
class DraftPersistBatchError(DraftPersistError): ...
class DraftPersistNetworkError(DraftPersistError): ...
```

### 2.4 Existing Supabase write pattern (material repository save)

```startLine:80:endLine:112:C:/Users/Yarkiller/PycharmPET-Projects/Digital_CDS/supabase-integration/src/supabase_integration/material_repository.py
    def save(self, material: Material) -> Material:
        payload = {
            "id": material.id,
            "slug": material.slug,
            "title": material.title,
            "dek": material.dek,
            "body_markdown": material.body_markdown,
            "format": material.format,
            "status": material.status.value,
            "reading_minutes": material.reading_minutes,
            "provenance_label": material.provenance_label,
            "source_id": material.source_id,
            "roles": list(material.roles),
            "published_at": material.published_at.isoformat() if material.published_at else None,
            "created_at": material.created_at.isoformat(),
            "updated_at": material.updated_at.isoformat(),
        }
        try:
            result = self._client.table("materials").upsert(payload).execute()
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise PersistenceError(f"materials save failed: {exc}") from exc

        data = getattr(result, "data", None) or []
        if not data:
            raise PersistenceError("materials upsert returned no rows")
        # Tags/relations are owned by seed/editorial paths; return domain object as saved.
        return material
```

**Mapping:** the Phase 9 adapter does not use `.table(...).upsert(...)`; it uses `.rpc("persist_draft_and_enqueue", {...}).execute()`. Error handling follows the same boundary pattern.

### 2.5 Existing batch-selection pattern

```startLine:62:endLine:80:C:/Users/Yarkiller/PycharmPET-Projects/Digital_CDS/supabase-integration/src/supabase_integration/shortlist_repository.py
    def get_current_batch(self) -> ShortlistBatch | None:
        try:
            result = (
                self._client.table("digest_shortlist_batches")
                .select("*")
                .is_("sent_at", "null")
                .order("week_start", desc=True)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001 — map SDK failures at boundary
            raise PersistenceError(f"shortlist get_current_batch failed: {exc}") from exc
```

**Mapping:** this logic moves into the RPC `persist_draft_and_enqueue`; the Python adapter only passes `p_batch_size` and material fields.

### 2.6 Existing mapper pattern (`captions`)

```startLine:1:endLine:70:C:/Users/Yarkiller/PycharmPET-Projects/Digital_CDS/ingestion-service/src/ingestion_service/mapping/captions.py
"""Map CaptionsError → IngestError(stage=captions) with locked reasons (D-10, D-13)."""

from __future__ import annotations

from typing import Any

from data_collection.errors.captions import (
    CaptionsBlocked,
    CaptionsBotChallenge,
    CaptionsDisabled,
    CaptionsEmpty,
    CaptionsError,
    CaptionsNetworkError,
    CaptionsNoPreferredLanguage,
    CaptionsUnavailable,
    CaptionsVideoUnavailable,
)
from ingestion_service.domain.errors import IngestError

CAPTIONS_REASONS: frozenset[str] = frozenset(
    {
        "no_captions",
        "no_preferred_language",
        "captions_disabled",
        "video_unavailable",
        "youtube_blocked",
        "bot_challenge",
        "network_error",
        "empty_captions",
        "unknown_captions_error",
    }
)

_CONTEXT_ALLOWLIST: frozenset[str] = frozenset(
    {
        "video_id",
        "available_languages",
        "exception_class",
    }
)

_REASON_BY_TYPE: dict[type[CaptionsError], str] = {
    CaptionsUnavailable: "no_captions",
    CaptionsNoPreferredLanguage: "no_preferred_language",
    CaptionsDisabled: "captions_disabled",
    CaptionsVideoUnavailable: "video_unavailable",
    CaptionsBlocked: "youtube_blocked",
    CaptionsBotChallenge: "bot_challenge",
    CaptionsNetworkError: "network_error",
    CaptionsEmpty: "empty_captions",
}


def _forward_context(error: CaptionsError) -> dict[str, Any]:
    forwarded: dict[str, Any] = {"video_id": error.video_id}
    raw = dict(error.context)
    for key in _CONTEXT_ALLOWLIST:
        if key == "video_id":
            continue
        if key in raw:
            forwarded[key] = raw[key]
    return forwarded


def map_captions_error(error: CaptionsError) -> IngestError:
    reason = _REASON_BY_TYPE.get(type(error), "unknown_captions_error")
    return IngestError(
        stage="captions",
        reason=reason,
        message=f"captions {reason} for {error.video_id}",
        context=_forward_context(error),
    )
```

**Mapping:** create `ingestion_service/mapping/persist.py` with `PERSIST_REASONS`, `_CONTEXT_ALLOWLIST = {"video_id", "slug", "batch_id", "reason"}`, and `map_persist_error(DraftPersistError) -> IngestError(stage="persist")`.

### 2.7 Existing `IngestError` shape

```startLine:1:endLine:40:C:/Users/Yarkiller/PycharmPET-Projects/Digital_CDS/ingestion-service/src/ingestion_service/domain/errors.py
"""Operator-facing ingest diagnostic errors (D-11, D-13)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Stage = Literal[
    "url",
    "captions",
    "metadata",
    "consistency",
    "llm",
    "llm_truncation",
    "persist",
]


@dataclass
class IngestError(Exception):
    stage: Stage
    reason: str
    message: str
    context: dict[str, Any] = field(default_factory=dict)
    exit_code: int = 1

    def __post_init__(self) -> None:
        Exception.__init__(self, self.message)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "ok": False,
            "stage": self.stage,
            "reason": self.reason,
            "message": self.message,
            "exit_code": self.exit_code,
        }
        if self.context:
            payload["context"] = self.context
        return payload
```

**Mapping:** `map_persist_error` returns `IngestError(stage="persist", reason=<locked>, ...)`.

### 2.8 Existing composition settings pattern

```startLine:30:endLine:60:C:/Users/Yarkiller/PycharmPET-Projects/Digital_CDS/ingestion-service/src/ingestion_service/composition/settings.py
@dataclass(frozen=True)
class Settings:
    youtube_proxy_url: str | None = None
    max_transcript_chars: int = _DEFAULT_MAX_TRANSCRIPT_CHARS
    deepseek_api_key: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-flash"

    @classmethod
    def from_env(cls, environ: dict[str, str] | None = None) -> Settings:
        env = environ if environ is not None else os.environ
        raw_proxy = env.get("YOUTUBE_PROXY_URL")
        proxy = raw_proxy.strip() if raw_proxy is not None else None
        proxy = proxy or None

        raw_key = env.get("DEEPSEEK_API_KEY")
        key = raw_key.strip() if raw_key is not None else None
        key = key or None

        raw_base = env.get("DEEPSEEK_BASE_URL")
        base_url = raw_base.strip() if raw_base is not None else "https://api.deepseek.com"

        raw_model = env.get("DEEPSEEK_MODEL")
        model = raw_model.strip() if raw_model is not None else "deepseek-flash"

        return cls(
            youtube_proxy_url=proxy,
            max_transcript_chars=_max_transcript_chars(env),
            deepseek_api_key=key,
            deepseek_base_url=base_url,
            deepseek_model=model,
        )
```

**Mapping:** add fields `supabase_url: str`, `supabase_secret_key: str`, `shortlist_batch_size: int = 5`; add a `_shortlist_batch_size(env)` validator (positive integer, raises `ConfigurationError`).

### 2.9 Existing composition client factory pattern

```startLine:50:endLine:70:C:/Users/Yarkiller/PycharmPET-Projects/Digital_CDS/ingestion-service/src/ingestion_service/composition/clients.py
def build_deepseek_article_generator(
    settings: Settings,
    template_root: object | None = None,
) -> DeepSeekArticleGenerator:
    import importlib.resources

    root = (
        template_root
        if template_root is not None
        else importlib.resources.files("data_collection.templates")
    )
    templates = load_article_templates(root)
    client = build_async_deepseek_client(
        settings.deepseek_api_key or "",
        settings.deepseek_base_url,
        _DEEPSEEK_TIMEOUT,
    )
    return DeepSeekArticleGenerator(
        client=client,
        model=settings.deepseek_model,
        templates=templates,
        max_transcript_chars=settings.max_transcript_chars,
    )
```

**Mapping:** add `build_supabase_service_client(settings)` and `build_supabase_draft_persister(settings)`:

```python
from supabase import create_client


def build_supabase_service_client(settings: Settings) -> Client:
    return create_client(settings.supabase_url, settings.supabase_secret_key)


def build_supabase_draft_persister(settings: Settings) -> SupabaseDraftPersister:
    client = build_supabase_service_client(settings)
    return SupabaseDraftPersister(client)
```

### 2.10 Existing dependency declaration

```startLine:1:endLine:10:C:/Users/Yarkiller/PycharmPET-Projects/Digital_CDS/ingestion-service/pyproject.toml
[project]
name = "ingestion-service"
version = "0.1.0"
description = "YouTube → LLM → Supabase ingestion CLI for Digest CDS"
requires-python = ">=3.12"
dependencies = [
    "data-collection",
    "openai>=3.0,<4",
]
```

**Mapping:** append `"supabase>=2.0,<3"` and, if `python-slugify` is chosen, `"python-slugify>=8.0,<9"`.

### 2.11 Existing `.env.example` contract test

```startLine:1:endLine:40:C:/Users/Yarkiller/PycharmPET-Projects/Digital_CDS/tests/unit/test_env_example.py
"""Committed .env.example lists Phase 1 keys and is not gitignored."""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_KEYS = (
    "SUPABASE_URL",
    "SUPABASE_PUBLISHABLE_KEY",
    "SUPABASE_SECRET_KEY",
    "SUPABASE_JWKS_URL",
    "SUPABASE_JWT_ISSUER",
    "API_CORS_ORIGINS",
    "ALLOWED_EMAIL_DOMAINS",
    "APP_CONTAINER",
    "VITE_SUPABASE_URL",
    "VITE_SUPABASE_PUBLISHABLE_KEY",
    "VITE_API_BASE_URL",
    "VITE_USE_MOCKS",
)


def test_env_example_lists_required_keys() -> None:
    path = REPO_ROOT / ".env.example"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    for key in REQUIRED_KEYS:
        assert f"{key}=" in text, f"missing {key}"
    assert "VITE_SUPABASE_SECRET" not in text
    assert "5173" in text and "5174" in text
```

**Mapping:** create `ingestion-service/.env.example` (the file currently does not exist) with at least `SUPABASE_URL=`, `SUPABASE_SECRET_KEY=`, `SHORTLIST_BATCH_SIZE=5`. This file is separate from the root `.env.example` and does not need to satisfy `test_env_example.py`.

---

## 3. Database migration

| # | File | Role | Data flow | Closest analog |
|---|------|------|-----------|----------------|
| 17 | `supabase-integration/migrations/007_phase9_persist_draft.sql` | Schema + atomic RPC | CLI/adapter → Postgres | `005_phase5_admin_shortlist.sql` RPC + grants |

### 3.1 Existing RPC pattern with grants

```startLine:20:endLine:100:C:/Users/Yarkiller/PycharmPET-Projects/Digital_CDS/supabase-integration/migrations/005_phase5_admin_shortlist.sql
-- ─── Atomic claim + publish RPC (SECURITY INVOKER; service_role only) ────────
-- Claims unsent batch, inserts digest_issues + items for approved∩ready, stamps delivery.
create or replace function public.claim_and_publish_digest(
  p_batch_id bigint,
  p_sent_at timestamptz,
  p_period_label text,
  p_title text,
  p_delivery_status text default 'stubbed',
  p_recipient_count int default 0
)
returns jsonb
language plpgsql
security invoker
set search_path = public
as $$
declare
  v_batch public.digest_shortlist_batches%rowtype;
  v_issue_id bigint;
  v_issue_number int;
  v_issue_url text;
  v_item_count int := 0;
begin
  update public.digest_shortlist_batches b
  set sent_at = p_sent_at
  where b.id = p_batch_id
    and b.sent_at is null
  returning b.* into v_batch;

  if not found then
    raise exception 'claim_and_publish_digest: batch % already sent or missing', p_batch_id
      using errcode = 'P0001';
  end if;

  select coalesce(max(i.number), 0) + 1 into v_issue_number
  from public.digest_issues i;

  insert into public.digest_issues (number, period_label, title, published_at)
  values (v_issue_number, p_period_label, p_title, p_sent_at)
  returning id into v_issue_id;

  insert into public.digest_issue_items (issue_id, material_id, position)
  select v_issue_id, si.material_id, si.rank
  from public.digest_shortlist_items si
  join public.materials m on m.id = si.material_id
  where si.batch_id = p_batch_id
    and si.decision = 'approved'
    and m.status = 'ready'
  order by si.rank;

  get diagnostics v_item_count = row_count;
  if v_item_count = 0 then
    raise exception 'claim_and_publish_digest: empty approved∩ready pool for batch %', p_batch_id
      using errcode = 'check_violation';
  end if;

  v_issue_url := '/issues/' || v_issue_number::text;

  update public.digest_shortlist_batches
  set
    delivery_status = p_delivery_status,
    recipient_count = coalesce(p_recipient_count, 0),
    published_issue_id = v_issue_id,
    issue_url = v_issue_url
  where id = p_batch_id;

  return jsonb_build_object(
    'batch_id', p_batch_id,
    'issue_id', v_issue_id,
    'issue_number', v_issue_number,
    'issue_url', v_issue_url,
    'delivery_status', p_delivery_status,
    'recipient_count', coalesce(p_recipient_count, 0),
    'item_count', v_item_count
  );
end;
$$;

-- Revoke from PUBLIC / anon / authenticated; grant execute to service_role only (T-05-17).
revoke all on function public.claim_and_publish_digest(
  bigint, timestamptz, text, text, text, int
) from public;
revoke all on function public.claim_and_publish_digest(
  bigint, timestamptz, text, text, text, int
) from anon, authenticated;
grant execute on function public.claim_and_publish_digest(
  bigint, timestamptz, text, text, text, int
) to service_role;
```

**Mapping:** migration 007 must:
1. `alter table materials add column if not exists source_url text not null;`
2. `alter table materials add column if not exists youtube_video_id text not null unique;`
3. `alter table materials add column if not exists source_author text not null;`
4. `alter table materials add column if not exists source_published_at timestamptz;`
5. `create or replace function public.persist_draft_and_enqueue(...)` that:
   - inserts into `materials` with `ON CONFLICT (youtube_video_id) DO NOTHING`,
   - selects existing or new `material_id`,
   - finds latest unsent batch or creates new one,
   - inserts `digest_shortlist_items` with `rank = max(rank)+1`,
   - returns `jsonb_build_object('material_id', ..., 'slug', ..., 'batch_id', ..., 'rank', ...)`.
6. Revoke from `public`, `anon`, `authenticated`; grant execute to `service_role`.

### 3.2 Existing base `materials` table shape

```startLine:88:endLine:106:C:/Users/Yarkiller/PycharmPET-Projects/Digital_CDS/supabase-integration/migrations/001_initial_schema.sql
create table if not exists materials (
  id bigint generated always as identity primary key,
  slug text not null unique,
  title text not null,
  dek text not null default '',
  body_markdown text not null,
  format text not null default 'статья' check (format = 'статья'),
  status material_status not null default 'draft',
  reading_minutes int not null default 0 check (reading_minutes >= 0),
  provenance_label text not null,
  source_id bigint references ingestion_sources (id) on delete set null,
  roles text[] not null default '{}',
  published_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
```

**Mapping:** the migration adds provenance columns and the unique constraint on `youtube_video_id`.

---

## 4. Tests to add/update

| # | Test file | Role | Closest analog |
|---|-----------|------|----------------|
| 18 | `tests/unit/test_article_draft_internal.py` | DTO contract for roles | Current article DTO test |
| 19 | `tests/unit/test_material_draft_dto.py` | DTO contract for roles | Current material DTO test |
| 20 | `tests/unit/test_assemble_material_draft.py` | Roles copied through assembler | Current assembler test |
| 21 | `tests/unit/test_deepseek_article_adapter.py` | Roles validation + fallback | Current DeepSeek adapter tests |
| 22 | `tests/unit/test_data_collection_public_api.py` | `ArticleDraft` stays off root export | Current negative export test |
| 23 | `tests/unit/test_persist_port.py` | Port contract + fake | `data_collection/ports` pattern + `FakeTranscriptProvider` |
| 24 | `tests/unit/test_persist_error_mapping.py` | Locked reasons + context allowlist | `test_captions_error_mapping.py` |
| 25 | `tests/unit/test_supabase_draft_persister_contract.py` | Adapter with mocked RPC | `test_supabase_shortlist_repository_contract.py` |
| 26 | `tests/unit/test_persist_draft_use_case.py` | Slug/reading_minutes/roles + port call | `test_assemble_material_draft.py` |
| 27 | `tests/unit/test_ingestion_settings.py` | Supabase env + batch size validation | `test_ingestion_settings.py` |
| 28 | `tests/unit/test_phase9_migration_007.py` | SQL contract | `test_phase5_migration_005.py` |

### 4.1 Existing error-mapping test pattern

```startLine:1:endLine:90:C:/Users/Yarkiller/PycharmPET-Projects/Digital_CDS/tests/unit/test_captions_error_mapping.py
"""RED→GREEN: CaptionsError → IngestError(stage=captions) locked reasons (CAP-02, D-10, D-13)."""

from __future__ import annotations

import pytest
from youtube_transcript_api import (
    AgeRestricted,
    CouldNotRetrieveTranscript,
    IpBlocked,
    NoTranscriptFound,
    PoTokenRequired,
    RequestBlocked,
    TranscriptsDisabled,
    VideoUnavailable,
    VideoUnplayable,
    YouTubeRequestFailed,
)

from data_collection.errors.captions import (
    CaptionsBlocked,
    CaptionsBotChallenge,
    CaptionsDisabled,
    CaptionsEmpty,
    CaptionsError,
    CaptionsNetworkError,
    CaptionsNoPreferredLanguage,
    CaptionsUnavailable,
    CaptionsVideoUnavailable,
)

VIDEO_ID = "dQw4w9WgXcQ"

LOCKED_REASONS = frozenset(
    {
        "no_captions",
        "no_preferred_language",
        "captions_disabled",
        "video_unavailable",
        "youtube_blocked",
        "bot_challenge",
        "network_error",
        "empty_captions",
        "unknown_captions_error",
    }
)

@pytest.mark.parametrize(
    ("error", "reason"),
    [
        (CaptionsUnavailable(VIDEO_ID), "no_captions"),
        (
            CaptionsNoPreferredLanguage(VIDEO_ID, ["de", "es"]),
            "no_preferred_language",
        ),
        (CaptionsDisabled(VIDEO_ID), "captions_disabled"),
        (CaptionsVideoUnavailable(VIDEO_ID), "video_unavailable"),
        (CaptionsBlocked(VIDEO_ID), "youtube_blocked"),
        (CaptionsBotChallenge(VIDEO_ID), "bot_challenge"),
        (CaptionsNetworkError(VIDEO_ID), "network_error"),
        (CaptionsEmpty(VIDEO_ID), "empty_captions"),
        (CaptionsError(VIDEO_ID), "unknown_captions_error"),
    ],
)
def test_map_captions_error_subtype_to_locked_reason(
    error: CaptionsError, reason: str
) -> None:
    from ingestion_service.mapping.captions import map_captions_error

    mapped = map_captions_error(error)

    assert mapped.stage == "captions"
    assert mapped.reason == reason
    assert mapped.context.get("video_id") == VIDEO_ID
    payload = mapped.to_dict()
    assert payload["ok"] is False
    assert payload["stage"] == "captions"
    assert payload["exit_code"] == 1
```

**Mapping for persist mapper test:** parametrize `DraftPersistError` subtypes → reasons; assert `stage="persist"`; assert context allowlist only `video_id`, `slug`, `batch_id`, `reason`; assert no secret leakage.

### 4.2 Existing Supabase adapter contract test pattern

```startLine:1:endLine:100:C:/Users/Yarkiller/PycharmPET-Projects/Digital_CDS/tests/unit/test_supabase_shortlist_repository_contract.py
"""Contract tests for SupabaseShortlistRepository (offline stubs — no network).

ADMIN-02 / ADMIN-07 / D-81 / D-87 — get_current_batch, set_decision, claim_sent.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

import pytest

from backend.domain.errors import AlreadySentError, PersistenceError, ShortlistNotFoundError


class _FakeExecuteResult:
    def __init__(self, data: list[dict[str, Any]]) -> None:
        self.data = data


class _FakeQuery:
    def __init__(self, table: "_FakeTable") -> None:
        self._table = table
        self._op: str | None = None
        self._payload: Any = None
        self._filters: list[tuple[str, Any]] = []
        self._is_null: list[str] = []
        self._orders: list[tuple[str, bool]] = []
        self._limit: int | None = None
        self._select_cols: str = "*"
```

**Mapping for adapter contract test:** stub `client.rpc(name, params).execute()` returning a fake `APIResponse` with `.data = {"material_id": 101, "slug": "...", "batch_id": 7, "rank": 3}`. Assert adapter returns `PersistResult(...)`. Add tests for exception paths raising `DraftPersistError` with correct reason.

### 4.3 Existing fake pattern

```startLine:50:endLine:80:C:/Users/Yarkiller/PycharmPET-Projects/Digital_CDS/data-collection/src/data_collection/tests_support/fakes.py
class FakeArticleGenerator:
    def __init__(
        self,
        result: ArticleDraft,
        failures: dict[str, ArticleError] | None = None,
    ) -> None:
        self._result = result
        self._failures = failures or {}
        self.calls: list[ArticleGeneratorCall] = []

    async def process(
        self, transcript: Transcript, template: TemplateKind
    ) -> ArticleDraft:
        self.calls.append({"transcript": transcript, "template": template})
        failure = self._failures.get(transcript.video_id)
        if failure is not None:
            raise failure
        return self._result
```

**Mapping for fake:** create in ingestion-service tests (or a new `ingestion_service.tests_support.fakes`) a `FakeDraftPersister` that records calls and supports scripted failures by `video_id`.

---

## 5. Cross-cutting concerns

### 5.1 Public API boundaries

- `data_collection.__all__` currently whitelists 7 names. `ArticleDraft` must **not** be exported from the root (analog: `test_data_collection_public_api.py`).
- `ingestion_service.mapping.__all__` currently lists 4 mappers; add `map_persist_error`.

### 5.2 Architecture guardrails

- No `supabase` import in `data-collection` or `backend` business logic (already enforced by architecture tests).
- No direct env access outside `ingestion_service/composition/settings.py`.
- Adapter errors are mapped at the boundary; use-case layer sees only `PersistResult` or `IngestError`.

### 5.3 TDD order suggested by research

1. Port + `PersistResult` contract test.
2. `DraftPersistError` + `map_persist_error` test.
3. Use-case happy-path test with fake port.
4. Use-case idempotency test with fake port.
5. Adapter contract test with mocked Supabase client.
6. Adapter error-mapping test.
7. Migration 007 SQL contract test.
8. Phase 8 amendments (roles) tests before adapter is wired.

## PATTERN MAPPING COMPLETE