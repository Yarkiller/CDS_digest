"""RED→GREEN: ArticleError → IngestError(stage=llm) with locked reasons (D-13)."""

from __future__ import annotations

from data_collection.errors.article import (
    ArticleAuthError,
    ArticleContextLengthError,
    ArticleInvalidDraft,
    ArticleInvalidJson,
    ArticleNetworkError,
    ArticleProviderError,
    ArticleUnknownError,
)
from ingestion_service.domain.errors import Stage
from ingestion_service.mapping.article import LLM_REASONS, map_article_error


def test_llm_reasons_is_exact_seven_reason_set() -> None:
    assert LLM_REASONS == frozenset(
        {
            "network_error",
            "provider_error",
            "auth_error",
            "invalid_json",
            "invalid_article_draft",
            "provider_context_length",
            "unknown_llm_error",
        }
    )


def test_article_network_error_maps_to_llm_network_error() -> None:
    error = ArticleNetworkError("vid1", exception_class="APITimeoutError")
    ingest = map_article_error(error)
    assert ingest.stage == "llm"
    assert ingest.reason == "network_error"
    assert ingest.message == "llm network_error"
    assert ingest.exit_code == 1
    assert ingest.to_dict()["ok"] is False


def test_article_provider_error_maps_to_llm_provider_error() -> None:
    error = ArticleProviderError("vid1", exception_class="RateLimitError")
    ingest = map_article_error(error)
    assert ingest.stage == "llm"
    assert ingest.reason == "provider_error"


def test_article_auth_error_maps_to_llm_auth_error() -> None:
    error = ArticleAuthError("vid1", exception_class="AuthenticationError")
    ingest = map_article_error(error)
    assert ingest.stage == "llm"
    assert ingest.reason == "auth_error"


def test_article_invalid_json_maps_to_llm_invalid_json() -> None:
    error = ArticleInvalidJson("vid1")
    ingest = map_article_error(error)
    assert ingest.stage == "llm"
    assert ingest.reason == "invalid_json"


def test_article_invalid_draft_maps_to_llm_invalid_article_draft() -> None:
    error = ArticleInvalidDraft("vid1")
    ingest = map_article_error(error)
    assert ingest.stage == "llm"
    assert ingest.reason == "invalid_article_draft"


def test_article_context_length_error_maps_to_provider_context_length() -> None:
    error = ArticleContextLengthError("vid1", exception_class="APIStatusError")
    ingest = map_article_error(error)
    assert ingest.stage == "llm"
    assert ingest.reason == "provider_context_length"


def test_article_unknown_error_maps_to_unknown_llm_error() -> None:
    error = ArticleUnknownError("vid1", exception_class="SomeError")
    ingest = map_article_error(error)
    assert ingest.stage == "llm"
    assert ingest.reason == "unknown_llm_error"


def test_article_budget_error_maps_to_llm_truncation() -> None:
    from data_collection.errors.article import ArticleBudgetError

    forbidden_transcript = "planted transcript text that must not appear"
    error = ArticleBudgetError(
        "vid1",
        char_count=100000,
        max_chars=80000,
        forbidden_transcript=forbidden_transcript,
    )
    ingest = map_article_error(error)
    assert ingest.stage == "llm_truncation"
    assert ingest.reason == "transcript_too_long"
    assert ingest.message == "llm_truncation transcript_too_long"
    assert ingest.exit_code == 1
    assert ingest.context == {"char_count": 100000, "max_chars": 80000}
    full = ingest.message + str(ingest.to_dict())
    assert forbidden_transcript not in full
    assert "video_id" not in ingest.context


def test_context_allowlist_excludes_transcript_and_key() -> None:
    forbidden_sentence = "This is the full transcript text planted by the test."
    forbidden_key = "sk-test-key-1234567890"
    error = ArticleNetworkError(
        "vid1",
        exception_class="APITimeoutError",
        status_code=599,
        forbidden_transcript=forbidden_sentence,
        forbidden_key=forbidden_key,
    )
    ingest = map_article_error(error)
    full = ingest.message + str(ingest.to_dict())
    assert forbidden_sentence not in full
    assert forbidden_key not in full
    assert ingest.context.keys() <= {"video_id", "exception_class", "status_code"}


def test_reasons_do_not_equal_sdk_class_names() -> None:
    error = ArticleNetworkError("vid1", exception_class="APITimeoutError")
    ingest = map_article_error(error)
    assert ingest.reason not in {"APITimeoutError", "APIConnectionError"}
    assert ingest.to_dict()["reason"] not in {"APITimeoutError", "APIConnectionError"}


def test_stage_set_unchanged() -> None:
    from typing import get_args

    assert set(get_args(Stage)) == {
        "url",
        "captions",
        "metadata",
        "consistency",
        "llm",
        "llm_truncation",
        "persist",
    }


def test_map_article_error_exported_from_mapping_package() -> None:
    from ingestion_service import mapping

    assert "map_article_error" in mapping.__all__
