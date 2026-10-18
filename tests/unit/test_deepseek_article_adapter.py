"""RED→GREEN: DeepSeek article adapter with an injected stub client (LLM-01, LLM-04)."""

from __future__ import annotations

import asyncio
import importlib.resources
import json
from dataclasses import dataclass
from typing import Any

import pytest
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    InternalServerError,
    PermissionDeniedError,
    RateLimitError,
)

from data_collection.dto.article_draft import ArticleDraft
from data_collection.dto.template_kind import TemplateKind
from data_collection.dto.transcript import Transcript


def _stub_client(content: str) -> Any:
    @dataclass
    class _Message:
        content: str

    @dataclass
    class _Choice:
        message: _Message

    @dataclass
    class _Response:
        choices: list[_Choice]

    class _Completions:
        def __init__(self) -> None:
            self.calls: list[dict[str, Any]] = []

        async def create(self, **kwargs: Any) -> Any:
            self.calls.append(kwargs)
            return _Response(choices=[_Choice(message=_Message(content=content))])

    class _Client:
        def __init__(self) -> None:
            self.chat = type("_Chat", (), {"completions": _Completions()})()

    return _Client()


def _make_transcript(language: str = "ru") -> Transcript:
    return Transcript(text="some transcript text", language=language, video_id="vid1")


def test_process_returns_article_draft_for_lecture() -> None:
    from data_collection.adapters.deepseek_article import DeepSeekArticleGenerator
    from data_collection.templates import load_article_templates

    templates = load_article_templates(importlib.resources.files("data_collection.templates"))
    payload = {
        "title": "Title",
        "dek": "Dek",
        "body_markdown": "# Body",
        "extra_key": "ignored",
    }
    client = _stub_client(json.dumps(payload))
    generator = DeepSeekArticleGenerator(
        client=client,
        model="deepseek-flash",
        templates=templates,
        max_transcript_chars=80000,
    )

    draft = asyncio.run(generator.process(_make_transcript("ru"), TemplateKind.LECTURE))

    assert isinstance(draft, ArticleDraft)
    assert draft.title == "Title"
    assert draft.dek == "Dek"
    assert draft.body_markdown == "# Body"
    assert not hasattr(draft, "extra_key")
    assert len(client.chat.completions.calls) == 1


def test_process_returns_article_draft_for_podcast() -> None:
    from data_collection.adapters.deepseek_article import DeepSeekArticleGenerator
    from data_collection.templates import load_article_templates

    templates = load_article_templates(importlib.resources.files("data_collection.templates"))
    payload = {
        "title": "Podcast Title",
        "dek": "Podcast Dek",
        "body_markdown": "## О чём разговор\n\nBody",
    }
    client = _stub_client(json.dumps(payload))
    generator = DeepSeekArticleGenerator(
        client=client,
        model="deepseek-flash",
        templates=templates,
        max_transcript_chars=80000,
    )

    draft = asyncio.run(generator.process(_make_transcript("en"), TemplateKind.PODCAST))

    assert draft.title == "Podcast Title"
    assert draft.dek == "Podcast Dek"
    assert draft.body_markdown == "## О чём разговор\n\nBody"


def test_lecture_prompt_contains_lecture_headings_not_podcast() -> None:
    from data_collection.adapters.deepseek_article import DeepSeekArticleGenerator
    from data_collection.templates import load_article_templates

    templates = load_article_templates(importlib.resources.files("data_collection.templates"))
    client = _stub_client(json.dumps({"title": "T", "dek": "D", "body_markdown": "B"}))
    generator = DeepSeekArticleGenerator(
        client=client,
        model="deepseek-flash",
        templates=templates,
        max_transcript_chars=80000,
    )

    asyncio.run(generator.process(_make_transcript("ru"), TemplateKind.LECTURE))

    call = client.chat.completions.calls[0]
    messages = call["messages"]
    user_content = messages[-1]["content"]
    assert "## Тезис" in user_content
    assert "## Ход рассуждения" in user_content
    assert "## Вывод" in user_content
    assert "## О чём разговор" not in user_content


def test_podcast_prompt_contains_podcast_headings_not_lecture() -> None:
    from data_collection.adapters.deepseek_article import DeepSeekArticleGenerator
    from data_collection.templates import load_article_templates

    templates = load_article_templates(importlib.resources.files("data_collection.templates"))
    client = _stub_client(json.dumps({"title": "T", "dek": "D", "body_markdown": "B"}))
    generator = DeepSeekArticleGenerator(
        client=client,
        model="deepseek-flash",
        templates=templates,
        max_transcript_chars=80000,
    )

    asyncio.run(generator.process(_make_transcript("en"), TemplateKind.PODCAST))

    call = client.chat.completions.calls[0]
    messages = call["messages"]
    user_content = messages[-1]["content"]
    assert "## О чём разговор" in user_content
    assert "## Позиции" in user_content
    assert "## Что запомнить" in user_content
    assert "## Тезис" not in user_content


def test_system_prompt_contains_honesty_and_language_rules() -> None:
    from data_collection.adapters.deepseek_article import DeepSeekArticleGenerator
    from data_collection.templates import load_article_templates

    templates = load_article_templates(importlib.resources.files("data_collection.templates"))
    client = _stub_client(json.dumps({"title": "T", "dek": "D", "body_markdown": "B"}))
    generator = DeepSeekArticleGenerator(
        client=client,
        model="deepseek-flash",
        templates=templates,
        max_transcript_chars=80000,
    )

    asyncio.run(generator.process(_make_transcript("ru"), TemplateKind.LECTURE))

    call = client.chat.completions.calls[0]
    messages = call["messages"]
    system_content = messages[0]["content"]
    assert "Use only the transcript" in system_content
    assert "Do not invent facts, names, or numbers" in system_content
    assert "Output is always Russian" in system_content
    assert "If the transcript language is ru: format only; do not translate" in system_content
    assert "If the transcript language is en: translate into Russian" in system_content
    assert "Preserve technical terms, proper names, library names, numbers, and units as written" in system_content
    assert "json" in system_content
    assert "title" in system_content
    assert "dek" in system_content
    assert "body_markdown" in system_content


def test_create_kwargs_include_json_object_and_disabled_thinking() -> None:
    from data_collection.adapters.deepseek_article import DeepSeekArticleGenerator
    from data_collection.templates import load_article_templates

    templates = load_article_templates(importlib.resources.files("data_collection.templates"))
    client = _stub_client(json.dumps({"title": "T", "dek": "D", "body_markdown": "B"}))
    generator = DeepSeekArticleGenerator(
        client=client,
        model="deepseek-flash",
        templates=templates,
        max_transcript_chars=80000,
    )

    asyncio.run(generator.process(_make_transcript("ru"), TemplateKind.LECTURE))

    call = client.chat.completions.calls[0]
    assert call["response_format"] == {"type": "json_object"}
    assert call["extra_body"] == {"thinking": {"type": "disabled"}}


def test_preserved_technical_terms_round_trip_unchanged() -> None:
    from data_collection.adapters.deepseek_article import DeepSeekArticleGenerator
    from data_collection.templates import load_article_templates

    templates = load_article_templates(importlib.resources.files("data_collection.templates"))
    body = "pgvector, RAG, embedding"
    payload = {"title": "T", "dek": "D", "body_markdown": body}
    client = _stub_client(json.dumps(payload))
    generator = DeepSeekArticleGenerator(
        client=client,
        model="deepseek-flash",
        templates=templates,
        max_transcript_chars=80000,
    )

    for language in ("ru", "en"):
        draft = asyncio.run(generator.process(_make_transcript(language), TemplateKind.LECTURE))
        assert draft.body_markdown == body


def test_body_without_headings_is_valid_when_strings_non_blank() -> None:
    from data_collection.adapters.deepseek_article import DeepSeekArticleGenerator
    from data_collection.templates import load_article_templates

    templates = load_article_templates(importlib.resources.files("data_collection.templates"))
    payload = {"title": "T", "dek": "D", "body_markdown": "plain body"}
    client = _stub_client(json.dumps(payload))
    generator = DeepSeekArticleGenerator(
        client=client,
        model="deepseek-flash",
        templates=templates,
        max_transcript_chars=80000,
    )

    draft = asyncio.run(generator.process(_make_transcript("ru"), TemplateKind.LECTURE))
    assert draft.body_markdown == "plain body"


class _FakeRequest:
    pass


class _FakeResponse:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code
        self.request = _FakeRequest()
        self.headers = {}


_FAKE_REQUEST = _FakeRequest()


def _status_error(status_code: int, body: dict[str, Any] | None = None) -> APIStatusError:
    return APIStatusError(
        "error",
        response=_FakeResponse(status_code),
        body=body or {},
    )


def _failing_stub_client(exc: Exception) -> Any:
    class _Completions:
        def __init__(self) -> None:
            self.calls: list[dict[str, Any]] = []

        async def create(self, **kwargs: Any) -> Any:
            self.calls.append(kwargs)
            raise exc

    class _Client:
        def __init__(self) -> None:
            self.chat = type("_Chat", (), {"completions": _Completions()})()

    return _Client()


def _make_generator(client: Any) -> Any:
    from data_collection.adapters.deepseek_article import DeepSeekArticleGenerator
    from data_collection.templates import load_article_templates

    templates = load_article_templates(importlib.resources.files("data_collection.templates"))
    return DeepSeekArticleGenerator(
        client=client,
        model="deepseek-flash",
        templates=templates,
        max_transcript_chars=80000,
    )


def test_timeout_error_raises_article_network_error() -> None:
    from data_collection.errors.article import ArticleNetworkError

    client = _failing_stub_client(APITimeoutError(request=_FAKE_REQUEST))
    generator = _make_generator(client)

    with pytest.raises(ArticleNetworkError):
        asyncio.run(generator.process(_make_transcript("ru"), TemplateKind.LECTURE))


def test_connection_error_raises_article_network_error() -> None:
    from data_collection.errors.article import ArticleNetworkError

    client = _failing_stub_client(APIConnectionError(request=_FAKE_REQUEST))
    generator = _make_generator(client)

    with pytest.raises(ArticleNetworkError):
        asyncio.run(generator.process(_make_transcript("ru"), TemplateKind.LECTURE))


def test_rate_limit_error_raises_article_provider_error_and_calls_create_once() -> None:
    from data_collection.errors.article import ArticleProviderError

    client = _failing_stub_client(RateLimitError("rate limit", response=_FakeResponse(429), body={}))
    generator = _make_generator(client)

    with pytest.raises(ArticleProviderError):
        asyncio.run(generator.process(_make_transcript("ru"), TemplateKind.LECTURE))
    assert len(client.chat.completions.calls) == 1


def test_internal_server_error_raises_article_provider_error() -> None:
    from data_collection.errors.article import ArticleProviderError

    client = _failing_stub_client(InternalServerError("server error", response=_FakeResponse(500), body={}))
    generator = _make_generator(client)

    with pytest.raises(ArticleProviderError):
        asyncio.run(generator.process(_make_transcript("ru"), TemplateKind.LECTURE))


def test_authentication_error_raises_article_auth_error() -> None:
    from data_collection.errors.article import ArticleAuthError

    client = _failing_stub_client(AuthenticationError("auth", response=_FakeResponse(401), body={}))
    generator = _make_generator(client)

    with pytest.raises(ArticleAuthError):
        asyncio.run(generator.process(_make_transcript("ru"), TemplateKind.LECTURE))


def test_permission_denied_error_raises_article_auth_error() -> None:
    from data_collection.errors.article import ArticleAuthError

    client = _failing_stub_client(PermissionDeniedError("denied", response=_FakeResponse(403), body={}))
    generator = _make_generator(client)

    with pytest.raises(ArticleAuthError):
        asyncio.run(generator.process(_make_transcript("ru"), TemplateKind.LECTURE))


def test_status_400_code_context_length_raises_article_context_length_error() -> None:
    from data_collection.errors.article import ArticleContextLengthError

    client = _failing_stub_client(_status_error(400, body={"code": "context_length_exceeded"}))
    generator = _make_generator(client)

    with pytest.raises(ArticleContextLengthError):
        asyncio.run(generator.process(_make_transcript("ru"), TemplateKind.LECTURE))


def test_status_400_type_context_length_raises_article_context_length_error() -> None:
    from data_collection.errors.article import ArticleContextLengthError

    client = _failing_stub_client(_status_error(400, body={"type": "context_length"}))
    generator = _make_generator(client)

    with pytest.raises(ArticleContextLengthError):
        asyncio.run(generator.process(_make_transcript("ru"), TemplateKind.LECTURE))


def test_status_402_raises_article_unknown_error() -> None:
    from data_collection.errors.article import ArticleUnknownError

    client = _failing_stub_client(_status_error(402, body={"code": "billing"}))
    generator = _make_generator(client)

    with pytest.raises(ArticleUnknownError):
        asyncio.run(generator.process(_make_transcript("ru"), TemplateKind.LECTURE))


def test_fenced_json_raises_article_invalid_json() -> None:
    from data_collection.errors.article import ArticleInvalidJson

    client = _stub_client('```json\n{"title":"T","dek":"D","body_markdown":"B"}\n```')
    generator = _make_generator(client)

    with pytest.raises(ArticleInvalidJson):
        asyncio.run(generator.process(_make_transcript("ru"), TemplateKind.LECTURE))


def test_null_content_raises_article_invalid_json() -> None:
    from data_collection.errors.article import ArticleInvalidJson

    @dataclass
    class _Message:
        content: str | None

    @dataclass
    class _Choice:
        message: _Message

    @dataclass
    class _Response:
        choices: list[_Choice]

    class _Completions:
        async def create(self, **kwargs: Any) -> Any:
            return _Response(choices=[_Choice(message=_Message(content=None))])

    class _Client:
        def __init__(self) -> None:
            self.chat = type("_Chat", (), {"completions": _Completions()})()

    generator = _make_generator(_Client())
    with pytest.raises(ArticleInvalidJson):
        asyncio.run(generator.process(_make_transcript("ru"), TemplateKind.LECTURE))


def test_empty_content_raises_article_invalid_json() -> None:
    from data_collection.errors.article import ArticleInvalidJson

    client = _stub_client("")
    generator = _make_generator(client)

    with pytest.raises(ArticleInvalidJson):
        asyncio.run(generator.process(_make_transcript("ru"), TemplateKind.LECTURE))


def test_empty_choices_raises_article_invalid_json() -> None:
    from data_collection.errors.article import ArticleInvalidJson

    @dataclass
    class _Response:
        choices: list[Any]

    class _Completions:
        async def create(self, **kwargs: Any) -> Any:
            return _Response(choices=[])

    class _Client:
        def __init__(self) -> None:
            self.chat = type("_Chat", (), {"completions": _Completions()})()

    generator = _make_generator(_Client())
    with pytest.raises(ArticleInvalidJson):
        asyncio.run(generator.process(_make_transcript("ru"), TemplateKind.LECTURE))


def test_json_array_raises_article_invalid_json() -> None:
    from data_collection.errors.article import ArticleInvalidJson

    client = _stub_client('["title","dek"]')
    generator = _make_generator(client)

    with pytest.raises(ArticleInvalidJson):
        asyncio.run(generator.process(_make_transcript("ru"), TemplateKind.LECTURE))


def test_blank_title_raises_article_invalid_draft() -> None:
    from data_collection.errors.article import ArticleInvalidDraft

    client = _stub_client('{"title":" ","dek":"D","body_markdown":"B"}')
    generator = _make_generator(client)

    with pytest.raises(ArticleInvalidDraft):
        asyncio.run(generator.process(_make_transcript("ru"), TemplateKind.LECTURE))


def test_missing_field_raises_article_invalid_draft() -> None:
    from data_collection.errors.article import ArticleInvalidDraft

    client = _stub_client('{"title":"T","body_markdown":"B"}')
    generator = _make_generator(client)

    with pytest.raises(ArticleInvalidDraft):
        asyncio.run(generator.process(_make_transcript("ru"), TemplateKind.LECTURE))


def test_gather_of_raising_and_successful_process_returns_only_success_draft() -> None:
    import asyncio

    from data_collection.errors.article import ArticleNetworkError

    success_client = _stub_client('{"title":"T","dek":"D","body_markdown":"B"}')
    fail_client = _failing_stub_client(APITimeoutError(request=_FAKE_REQUEST))

    success_generator = _make_generator(success_client)
    fail_generator = _make_generator(fail_client)

    async def _run() -> tuple[Any, Any]:
        return await asyncio.gather(
            fail_generator.process(_make_transcript("ru"), TemplateKind.LECTURE),
            success_generator.process(_make_transcript("ru"), TemplateKind.LECTURE),
            return_exceptions=True,
        )

    results = asyncio.run(_run())
    assert isinstance(results[0], ArticleNetworkError)
    assert isinstance(results[1], ArticleDraft)
    assert results[1].title == "T"


def test_exactly_max_chars_calls_create() -> None:
    from data_collection.adapters.deepseek_article import DeepSeekArticleGenerator
    from data_collection.templates import load_article_templates

    templates = load_article_templates(importlib.resources.files("data_collection.templates"))
    client = _stub_client('{"title":"T","dek":"D","body_markdown":"B"}')
    generator = DeepSeekArticleGenerator(
        client=client,
        model="deepseek-flash",
        templates=templates,
        max_transcript_chars=5,
    )

    transcript = Transcript(text="12345", language="ru", video_id="vid1")
    asyncio.run(generator.process(transcript, TemplateKind.LECTURE))
    assert len(client.chat.completions.calls) == 1


def test_over_max_chars_does_not_call_create() -> None:
    from data_collection.adapters.deepseek_article import DeepSeekArticleGenerator
    from data_collection.errors.article import ArticleBudgetError
    from data_collection.templates import load_article_templates

    templates = load_article_templates(importlib.resources.files("data_collection.templates"))
    client = _stub_client('{"title":"T","dek":"D","body_markdown":"B"}')
    generator = DeepSeekArticleGenerator(
        client=client,
        model="deepseek-flash",
        templates=templates,
        max_transcript_chars=5,
    )

    transcript = Transcript(text="123456", language="ru", video_id="vid1")
    with pytest.raises(ArticleBudgetError):
        asyncio.run(generator.process(transcript, TemplateKind.LECTURE))
    assert len(client.chat.completions.calls) == 0


def test_long_template_with_short_transcript_does_not_raise_budget_error() -> None:
    from data_collection.adapters.deepseek_article import DeepSeekArticleGenerator
    from data_collection.templates import load_article_templates

    templates = load_article_templates(importlib.resources.files("data_collection.templates"))
    client = _stub_client('{"title":"T","dek":"D","body_markdown":"B"}')
    generator = DeepSeekArticleGenerator(
        client=client,
        model="deepseek-flash",
        templates={kind: "x" * 1000 for kind in templates},
        max_transcript_chars=10,
    )

    transcript = Transcript(text="1234567890", language="ru", video_id="vid1")
    asyncio.run(generator.process(transcript, TemplateKind.LECTURE))
    assert len(client.chat.completions.calls) == 1


def test_eighty_thousand_cyrillic_chars_call_create() -> None:
    from data_collection.adapters.deepseek_article import DeepSeekArticleGenerator
    from data_collection.templates import load_article_templates

    templates = load_article_templates(importlib.resources.files("data_collection.templates"))
    client = _stub_client('{"title":"T","dek":"D","body_markdown":"B"}')
    generator = DeepSeekArticleGenerator(
        client=client,
        model="deepseek-flash",
        templates=templates,
        max_transcript_chars=80000,
    )

    text = "я" * 80000
    transcript = Transcript(text=text, language="ru", video_id="vid1")
    asyncio.run(generator.process(transcript, TemplateKind.LECTURE))
    assert len(client.chat.completions.calls) == 1


def test_process_keeps_valid_roles_from_json_payload() -> None:
    client = _stub_client(
        json.dumps(
            {
                "title": "t",
                "dek": "d",
                "body_markdown": "b",
                "roles": ["ds", "employee"],
            }
        )
    )
    draft = asyncio.run(
        _make_generator(client).process(_make_transcript("ru"), TemplateKind.LECTURE)
    )
    assert draft.roles == ["ds", "employee"]


def test_process_filters_invalid_roles_from_json_payload() -> None:
    client = _stub_client(
        json.dumps(
            {
                "title": "t",
                "dek": "d",
                "body_markdown": "b",
                "roles": ["manager", "employee"],
            }
        )
    )
    draft = asyncio.run(
        _make_generator(client).process(_make_transcript("ru"), TemplateKind.LECTURE)
    )
    assert draft.roles == ["employee"]


def test_process_missing_roles_falls_back_to_employee() -> None:
    client = _stub_client(json.dumps({"title": "t", "dek": "d", "body_markdown": "b"}))
    draft = asyncio.run(
        _make_generator(client).process(_make_transcript("ru"), TemplateKind.LECTURE)
    )
    assert draft.roles == ["employee"]


def test_process_empty_roles_falls_back_to_employee() -> None:
    client = _stub_client(
        json.dumps({"title": "t", "dek": "d", "body_markdown": "b", "roles": []})
    )
    draft = asyncio.run(
        _make_generator(client).process(_make_transcript("ru"), TemplateKind.LECTURE)
    )
    assert draft.roles == ["employee"]


def test_process_single_ds_role_round_trips() -> None:
    client = _stub_client(
        json.dumps({"title": "t", "dek": "d", "body_markdown": "b", "roles": ["ds"]})
    )
    draft = asyncio.run(
        _make_generator(client).process(_make_transcript("ru"), TemplateKind.LECTURE)
    )
    assert draft.roles == ["ds"]
