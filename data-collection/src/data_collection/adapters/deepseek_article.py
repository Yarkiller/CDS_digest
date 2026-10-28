"""DeepSeek ArticleGenerator adapter via the official OpenAI SDK (D-11, D-12, D-13)."""

from __future__ import annotations

import json
from typing import Any

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    InternalServerError,
    PermissionDeniedError,
    RateLimitError,
)
from pydantic import ValidationError

from data_collection.dto.article_draft import ArticleDraft
from data_collection.dto.role_kind import normalize_roles
from data_collection.dto.template_kind import TemplateKind
from data_collection.dto.transcript import Transcript
from data_collection.errors.article import (
    ArticleAuthError,
    ArticleBudgetError,
    ArticleContextLengthError,
    ArticleInvalidDraft,
    ArticleInvalidJson,
    ArticleNetworkError,
    ArticleProviderError,
    ArticleUnknownError,
)


ARTICLE_SYSTEM_PROMPT = (
    "You are an editorial assistant preparing articles for СВА (Служба внутреннего аудита).\n"
    "Ground the talk in the transcript. Do not invent names, numbers, tools or versions the speaker stated.\n"
    "You may add textbook definitions of hard terms, short footnotes, and reference data that make a figure or claim readable; never present that added context as the speaker's words.\n"
    "Output is always Russian.\n"
    "If the transcript language is ru: format only; do not translate.\n"
    "If the transcript language is en: translate into Russian.\n"
    "Preserve technical terms, proper names, library names, numbers, and units as written.\n"
    "Write in the voice of the edition: state the substance, do not report the container. "
    "Never write «в подкасте рассказывается», «монолог содержит» or «в ролике говорится»; "
    "attribute a claim to the speaker by name instead («Элен считает…»).\n"
    "Editorial inference is allowed in ## Зачем это СВА and in definitions, footnotes and reference notes; "
    "never present it as the speaker's words and never invent a duty, a standard or a number the talk asserted.\n"
    "dek is a 1-2 sentence hook about the talk, never a summary and never the audit takeaway.\n"
    "Aim for 1200-1800 words; do not pad to fill space.\n"
    "Return one json object with keys title, dek, body_markdown, roles."
)


def build_article_messages(
    transcript: Transcript,
    template: TemplateKind,
    templates: dict[TemplateKind, str],
) -> list[dict[str, str]]:
    """System prompt + user message carrying template, language, and transcript."""
    user_parts = [
        templates[template],
        "",
        f"Transcript language: {transcript.language}",
        "",
        transcript.text,
    ]
    return [
        {"role": "system", "content": ARTICLE_SYSTEM_PROMPT},
        {"role": "user", "content": "\n".join(user_parts)},
    ]


def _exception_class(exc: BaseException) -> str:
    return type(exc).__name__


def _is_context_length_error(exc: APIStatusError) -> bool:
    if getattr(exc, "status_code", None) != 400:
        return False
    code = str(getattr(exc, "code", "") or "").lower()
    type_token = str(getattr(exc, "type", "") or "").lower()
    return "context_length" in code or "context_length" in type_token


class DeepSeekArticleGenerator:
    """ArticleGenerator implementation over an injected async OpenAI client."""

    def __init__(
        self,
        client: Any,
        model: str,
        templates: dict[TemplateKind, str],
        max_transcript_chars: int,
    ) -> None:
        self._client = client
        self._model = model
        self._templates = templates
        self._max_transcript_chars = max_transcript_chars

    async def process(
        self, transcript: Transcript, template: TemplateKind
    ) -> ArticleDraft:
        if len(transcript.text) > self._max_transcript_chars:
            raise ArticleBudgetError(
                transcript.video_id,
                char_count=len(transcript.text),
                max_chars=self._max_transcript_chars,
            )
        messages = build_article_messages(transcript, template, self._templates)
        content = await self._stream_content(transcript, messages)
        if not isinstance(content, str) or content == "":
            raise ArticleInvalidJson(transcript.video_id)

        try:
            payload = json.loads(content)
        except (json.JSONDecodeError, ValueError, TypeError) as exc:
            raise ArticleInvalidJson(transcript.video_id) from exc

        if not isinstance(payload, dict):
            raise ArticleInvalidJson(transcript.video_id)

        try:
            draft = ArticleDraft.model_validate(payload)
        except ValidationError as exc:
            raise ArticleInvalidDraft(
                transcript.video_id,
                exception_class=_exception_class(exc),
            ) from exc
        draft.roles = normalize_roles(draft.roles)
        return draft

    async def _stream_content(
        self, transcript: Transcript, messages: list[dict[str, str]]
    ) -> str:
        """Stream deltas and join them: a non-streaming call keeps the socket idle
        for 8-12 s on long articles, which middleboxes reset (APIConnectionError)."""
        parts: list[str] = []
        try:
            stream = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                response_format={"type": "json_object"},
                extra_body={"thinking": {"type": "disabled"}},
                stream=True,
            )
            async for chunk in stream:
                choices = getattr(chunk, "choices", None) or []
                if not choices:
                    continue
                delta = getattr(choices[0], "delta", None)
                text = getattr(delta, "content", None)
                if isinstance(text, str) and text:
                    parts.append(text)
        except APITimeoutError as exc:
            raise ArticleNetworkError(
                transcript.video_id,
                exception_class=_exception_class(exc),
            ) from exc
        except APIConnectionError as exc:
            raise ArticleNetworkError(
                transcript.video_id,
                exception_class=_exception_class(exc),
            ) from exc
        except (RateLimitError, InternalServerError) as exc:
            raise ArticleProviderError(
                transcript.video_id,
                exception_class=_exception_class(exc),
                status_code=getattr(exc, "status_code", None),
            ) from exc
        except (AuthenticationError, PermissionDeniedError) as exc:
            raise ArticleAuthError(
                transcript.video_id,
                exception_class=_exception_class(exc),
                status_code=getattr(exc, "status_code", None),
            ) from exc
        except APIStatusError as exc:
            if _is_context_length_error(exc):
                raise ArticleContextLengthError(
                    transcript.video_id,
                    exception_class=_exception_class(exc),
                    status_code=getattr(exc, "status_code", None),
                ) from exc
            raise ArticleUnknownError(
                transcript.video_id,
                exception_class=_exception_class(exc),
                status_code=getattr(exc, "status_code", None),
            ) from exc
        except Exception as exc:
            raise ArticleUnknownError(
                transcript.video_id,
                exception_class=_exception_class(exc),
            ) from exc
        return "".join(parts)
