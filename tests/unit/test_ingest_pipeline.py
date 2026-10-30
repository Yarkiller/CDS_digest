"""RED→GREEN: CONSISTENCY-01, provenance suffix, captions-then-metadata, CAP-02 (CLI-04)."""

from __future__ import annotations

import asyncio
import inspect

import pytest
from data_collection.dto.article_draft import ArticleDraft
from data_collection.dto.template_kind import TemplateKind
from data_collection.dto.transcript import Transcript
from data_collection.dto.video_metadata import VideoMetadata
from data_collection.errors.article import ArticleNetworkError
from data_collection.errors.captions import CaptionsUnavailable
from data_collection.tests_support.fakes import (
    FakeArticleGenerator,
    FakeTopicKindClassifier,
    FakeTranscriptProvider,
    FakeVideoMetadataProvider,
)
from ingestion_service.application.ports.persist import PersistResult
from ingestion_service.application.use_cases.ingest_pipeline import run_ingest_pipeline
from ingestion_service.domain.errors import IngestError
from ingestion_service.provenance import ENGLISH_TRANSLATION_SUFFIX
from ingestion_service.tests_support.fakes import FakeDraftPersister, RecordingDiagnostics

VIDEO_ID = "dQw4w9WgXcQ"
OTHER_VIDEO_ID = "oHg5SJYRHA0"
URL = f"https://youtu.be/{VIDEO_ID}"


def _transcript(*, language: str = "ru", video_id: str = VIDEO_ID) -> Transcript:
    return Transcript(text="ok captions", language=language, video_id=video_id)


def _article() -> ArticleDraft:
    return ArticleDraft(title="T", dek="D", body_markdown="B")


def _metadata(*, video_id: str = VIDEO_ID, author: str = "Rick Astley") -> VideoMetadata:
    return VideoMetadata(
        video_id=video_id,
        source_url=f"https://www.youtube.com/watch?v={video_id}",
        author=author,
    )


def _persist() -> FakeDraftPersister:
    return FakeDraftPersister(
        PersistResult(material_id=1, slug="t-dQw4w9WgXcQ", batch_id=1, rank=1)
    )


def _classifier(
    result: object = "conceptual",
    failures: dict[str, Exception] | None = None,
) -> FakeTopicKindClassifier:
    return FakeTopicKindClassifier(result=result, failures=failures)


def test_consistency_mismatch_raises_before_llm_and_persist() -> None:
    """CONSISTENCY-01: mismatched ids → stage=consistency, reason=video_id_mismatch."""
    captions = FakeTranscriptProvider(result=_transcript(video_id=VIDEO_ID))
    metadata = FakeVideoMetadataProvider(result=_metadata(video_id=OTHER_VIDEO_ID))
    article = FakeArticleGenerator(result=_article())
    persist = _persist()

    with pytest.raises(IngestError) as exc_info:
        asyncio.run(
            run_ingest_pipeline(
                URL,
                TemplateKind.LECTURE,
                captions=captions,
                metadata_provider=metadata,
                article=article,
                persist=persist,
                classifier=_classifier(),
            )
        )

    err = exc_info.value
    assert err.stage == "consistency"
    assert err.reason == "video_id_mismatch"
    assert set(err.context.keys()) == {"transcript_video_id", "metadata_video_id"}
    assert err.context["transcript_video_id"] == VIDEO_ID
    assert err.context["metadata_video_id"] == OTHER_VIDEO_ID
    assert article.calls == []
    assert persist.calls == []


def test_captions_failure_leaves_article_and_persist_empty() -> None:
    """CAP-02 through full pipeline: captions failure → no LLM, no persist."""
    captions = FakeTranscriptProvider(
        result=_transcript(),
        failures={VIDEO_ID: CaptionsUnavailable(VIDEO_ID)},
    )
    metadata = FakeVideoMetadataProvider(result=_metadata())
    article = FakeArticleGenerator(result=_article())
    persist = _persist()

    with pytest.raises(IngestError) as exc_info:
        asyncio.run(
            run_ingest_pipeline(
                URL,
                TemplateKind.LECTURE,
                captions=captions,
                metadata_provider=metadata,
                article=article,
                persist=persist,
                classifier=_classifier(),
            )
        )

    assert exc_info.value.stage == "captions"
    assert article.calls == []
    assert persist.calls == []
    assert metadata.calls == []


def test_captions_fetched_before_metadata() -> None:
    """Phase 7 D-24: captions.get awaited before metadata.get."""
    order: list[str] = []

    class OrderCaptions(FakeTranscriptProvider):
        async def get(self, video_id: str) -> Transcript:
            order.append("captions")
            return await super().get(video_id)

    class OrderMetadata(FakeVideoMetadataProvider):
        async def get(self, video_id: str) -> VideoMetadata:
            order.append("metadata")
            return await super().get(video_id)

    captions = OrderCaptions(result=_transcript())
    metadata = OrderMetadata(result=_metadata())
    article = FakeArticleGenerator(result=_article())
    persist = _persist()

    asyncio.run(
        run_ingest_pipeline(
            URL,
            TemplateKind.LECTURE,
            captions=captions,
            metadata_provider=metadata,
            article=article,
            persist=persist,
            classifier=_classifier(),
        )
    )

    assert order == ["captions", "metadata"]


def test_english_transcript_appends_translation_suffix() -> None:
    """Phase 8 D-05: language != ru → provenance ends with ENGLISH_TRANSLATION_SUFFIX."""
    captions = FakeTranscriptProvider(result=_transcript(language="en"))
    metadata = FakeVideoMetadataProvider(result=_metadata(author="Channel X"))
    article = FakeArticleGenerator(result=_article())
    persist = _persist()

    asyncio.run(
        run_ingest_pipeline(
            URL,
            TemplateKind.LECTURE,
            captions=captions,
            metadata_provider=metadata,
            article=article,
            persist=persist,
            classifier=_classifier(),
        )
    )

    assert len(persist.calls) == 1
    label = persist.calls[0].provenance_label
    assert label.endswith(ENGLISH_TRANSLATION_SUFFIX)
    assert label.startswith("YouTube · Channel X")


def test_russian_transcript_omits_translation_suffix() -> None:
    """Phase 8 D-05: language=ru → YouTube · {author} without suffix."""
    captions = FakeTranscriptProvider(result=_transcript(language="ru"))
    metadata = FakeVideoMetadataProvider(result=_metadata(author="Channel X"))
    article = FakeArticleGenerator(result=_article())
    persist = _persist()

    asyncio.run(
        run_ingest_pipeline(
            URL,
            TemplateKind.LECTURE,
            captions=captions,
            metadata_provider=metadata,
            article=article,
            persist=persist,
            classifier=_classifier(),
        )
    )

    assert len(persist.calls) == 1
    assert persist.calls[0].provenance_label == "YouTube · Channel X"
    assert ENGLISH_TRANSLATION_SUFFIX not in persist.calls[0].provenance_label


def test_pipeline_emits_stage_events_in_order() -> None:
    """D-04: start→complete fires for captions, metadata, llm, persist (in order)."""
    diagnostics = RecordingDiagnostics()
    captions = FakeTranscriptProvider(result=_transcript())
    metadata = FakeVideoMetadataProvider(result=_metadata())
    article = FakeArticleGenerator(result=_article())
    persist = _persist()

    result = asyncio.run(
        run_ingest_pipeline(
            URL,
            TemplateKind.LECTURE,
            captions=captions,
            metadata_provider=metadata,
            article=article,
            persist=persist,
            diagnostics=diagnostics,
            classifier=_classifier(),
        )
    )

    order = [(call[0], call[1]) for call in diagnostics.calls]
    assert order == [
        ("started", "captions"),
        ("completed", "captions"),
        ("started", "metadata"),
        ("completed", "metadata"),
        ("started", "llm"),
        ("completed", "llm"),
        ("started", "persist"),
        ("completed", "persist"),
    ]

    completed = {
        call[1]: call[2]
        for call in diagnostics.calls
        if call[0] == "completed" and len(call) > 2
    }
    # D-06: the metadata line exposes only video_id.
    assert completed["metadata"] == {"video_id": VIDEO_ID}
    # D-04: llm carries template + response length; persist carries the identifiers.
    assert completed["llm"] == {"template": "lecture", "response_chars": len("B")}
    assert completed["persist"]["material_id"] == result.material_id
    assert completed["persist"]["batch_id"] == result.batch_id
    assert completed["persist"]["rank"] == result.rank
    assert completed["persist"]["already_saved"] == result.already_saved


def test_captions_failure_records_stage_failed() -> None:
    """D-10: a captions failure emits stage_failed with the mapped reason/exit code."""
    diagnostics = RecordingDiagnostics()
    captions = FakeTranscriptProvider(
        result=_transcript(),
        failures={VIDEO_ID: CaptionsUnavailable(VIDEO_ID)},
    )

    with pytest.raises(IngestError):
        asyncio.run(
            run_ingest_pipeline(
                URL,
                TemplateKind.LECTURE,
                captions=captions,
                metadata_provider=FakeVideoMetadataProvider(result=_metadata()),
                article=FakeArticleGenerator(result=_article()),
                persist=_persist(),
                diagnostics=diagnostics,
                classifier=_classifier(),
            )
        )

    assert diagnostics.calls == [
        ("started", "captions"),
        ("failed", "captions", "no_captions", 1),
    ]


def test_article_failure_records_stage_failed_after_completed_stages() -> None:
    """D-10/D-11: completed stages precede stage_failed(llm, network_error, 1)."""
    diagnostics = RecordingDiagnostics()
    article = FakeArticleGenerator(
        result=_article(),
        failures={VIDEO_ID: ArticleNetworkError(VIDEO_ID)},
    )

    with pytest.raises(IngestError):
        asyncio.run(
            run_ingest_pipeline(
                URL,
                TemplateKind.LECTURE,
                captions=FakeTranscriptProvider(result=_transcript()),
                metadata_provider=FakeVideoMetadataProvider(result=_metadata()),
                article=article,
                persist=_persist(),
                diagnostics=diagnostics,
                classifier=_classifier(),
            )
        )

    projection = [(call[0], call[1]) for call in diagnostics.calls]
    assert projection == [
        ("started", "captions"),
        ("completed", "captions"),
        ("started", "metadata"),
        ("completed", "metadata"),
        ("started", "llm"),
        ("failed", "llm"),
    ]
    assert diagnostics.calls[-1] == ("failed", "llm", "network_error", 1)


def test_invalid_url_records_stage_failed_without_stage_start() -> None:
    """RESEARCH Pattern 4: a url failure fires before any stage started."""
    diagnostics = RecordingDiagnostics()

    with pytest.raises(IngestError) as exc_info:
        asyncio.run(
            run_ingest_pipeline(
                "https://example.com/watch?v=dQw4w9WgXcQ",
                TemplateKind.LECTURE,
                captions=FakeTranscriptProvider(result=_transcript()),
                metadata_provider=FakeVideoMetadataProvider(result=_metadata()),
                article=FakeArticleGenerator(result=_article()),
                persist=_persist(),
                diagnostics=diagnostics,
                classifier=_classifier(),
            )
        )

    assert exc_info.value.stage == "url"
    assert diagnostics.calls == [
        ("failed", "url", exc_info.value.reason, exc_info.value.exit_code),
    ]


def test_run_ingest_pipeline_requires_classifier() -> None:
    param = inspect.signature(run_ingest_pipeline).parameters["classifier"]
    assert param.default is inspect.Parameter.empty
    assert param.kind is inspect.Parameter.KEYWORD_ONLY


def test_fake_practical_persists_practical() -> None:
    persist = _persist()
    asyncio.run(
        run_ingest_pipeline(
            URL,
            TemplateKind.LECTURE,
            captions=FakeTranscriptProvider(result=_transcript()),
            metadata_provider=FakeVideoMetadataProvider(result=_metadata()),
            article=FakeArticleGenerator(result=_article()),
            persist=persist,
            classifier=_classifier(result="practical"),
        )
    )
    assert persist.calls[0].topic_kind == "practical"


@pytest.mark.parametrize("raw", ["unsure", None, "howto", {"kind": "practical"}])
def test_classifier_non_allowlist_persists_conceptual(raw: object) -> None:
    persist = _persist()
    asyncio.run(
        run_ingest_pipeline(
            URL,
            TemplateKind.LECTURE,
            captions=FakeTranscriptProvider(result=_transcript()),
            metadata_provider=FakeVideoMetadataProvider(result=_metadata()),
            article=FakeArticleGenerator(result=_article()),
            persist=persist,
            classifier=_classifier(result=raw),
        )
    )
    assert persist.calls[0].topic_kind == "conceptual"


def test_classifier_runtime_error_persists_conceptual_without_ingest_error() -> None:
    persist = _persist()
    diagnostics = RecordingDiagnostics()
    asyncio.run(
        run_ingest_pipeline(
            URL,
            TemplateKind.LECTURE,
            captions=FakeTranscriptProvider(result=_transcript()),
            metadata_provider=FakeVideoMetadataProvider(result=_metadata()),
            article=FakeArticleGenerator(result=_article()),
            persist=persist,
            diagnostics=diagnostics,
            classifier=_classifier(failures={VIDEO_ID: RuntimeError("boom")}),
        )
    )
    assert persist.calls[0].topic_kind == "conceptual"
    failed = [call for call in diagnostics.calls if call[0] == "failed"]
    assert failed == []
    stages = [call[1] for call in diagnostics.calls]
    assert "llm" in stages
    assert stages[-2:] == ["persist", "persist"]


def test_classifier_stamp_overwrites_leaked_pass1_topic_kind() -> None:
    persist = _persist()
    asyncio.run(
        run_ingest_pipeline(
            URL,
            TemplateKind.LECTURE,
            captions=FakeTranscriptProvider(result=_transcript()),
            metadata_provider=FakeVideoMetadataProvider(result=_metadata()),
            article=FakeArticleGenerator(
                result=ArticleDraft(
                    title="T", dek="D", body_markdown="B", topic_kind="practical"
                )
            ),
            persist=persist,
            classifier=_classifier(result="conceptual"),
        )
    )
    assert persist.calls[0].topic_kind == "conceptual"


def test_ambiguous_howto_fake_practical_is_stored_practical() -> None:
    persist = _persist()
    asyncio.run(
        run_ingest_pipeline(
            URL,
            TemplateKind.LECTURE,
            captions=FakeTranscriptProvider(
                result=Transcript(
                    text="maybe a how-to, maybe theory of the stack",
                    language="ru",
                    video_id=VIDEO_ID,
                )
            ),
            metadata_provider=FakeVideoMetadataProvider(result=_metadata()),
            article=FakeArticleGenerator(result=_article()),
            persist=persist,
            classifier=_classifier(result="practical"),
        )
    )
    assert persist.calls[0].topic_kind == "practical"


def test_theory_talk_fake_conceptual_is_scripted_not_inferred() -> None:
    persist = _persist()
    classifier = _classifier(result="conceptual")
    transcript = Transcript(
        text="how to install kubernetes include links and tools",
        language="ru",
        video_id=VIDEO_ID,
    )
    asyncio.run(
        run_ingest_pipeline(
            URL,
            TemplateKind.LECTURE,
            captions=FakeTranscriptProvider(result=transcript),
            metadata_provider=FakeVideoMetadataProvider(result=_metadata()),
            article=FakeArticleGenerator(result=_article()),
            persist=persist,
            classifier=classifier,
        )
    )
    assert persist.calls[0].topic_kind == "conceptual"
    assert classifier.calls[0]["transcript"] is transcript


def test_pipeline_on_stage_names_stay_transcript_llm_saved() -> None:
    stages: list[str] = []
    asyncio.run(
        run_ingest_pipeline(
            URL,
            TemplateKind.LECTURE,
            captions=FakeTranscriptProvider(result=_transcript()),
            metadata_provider=FakeVideoMetadataProvider(result=_metadata()),
            article=FakeArticleGenerator(result=_article()),
            persist=_persist(),
            on_stage=stages.append,
            classifier=_classifier(result="practical"),
        )
    )
    assert stages == ["transcript", "llm", "saved"]


def test_classifier_does_not_emit_classify_diagnostic_or_stage_failed() -> None:
    diagnostics = RecordingDiagnostics()
    asyncio.run(
        run_ingest_pipeline(
            URL,
            TemplateKind.LECTURE,
            captions=FakeTranscriptProvider(result=_transcript()),
            metadata_provider=FakeVideoMetadataProvider(result=_metadata()),
            article=FakeArticleGenerator(result=_article()),
            persist=_persist(),
            diagnostics=diagnostics,
            classifier=_classifier(result="practical"),
        )
    )
    order = [(call[0], call[1]) for call in diagnostics.calls]
    assert order == [
        ("started", "captions"),
        ("completed", "captions"),
        ("started", "metadata"),
        ("completed", "metadata"),
        ("started", "llm"),
        ("completed", "llm"),
        ("started", "persist"),
        ("completed", "persist"),
    ]
    assert all(call[1] != "classify" for call in diagnostics.calls)
    assert all(call[0] != "failed" for call in diagnostics.calls)


@pytest.mark.parametrize(
    "body",
    ["## Гайд\n", "## Гайд\n\n1. Open SAP"],
    ids=["empty-guide", "filled-guide"],
)
def test_furniture_only_guide_body_still_persists(body: str) -> None:
    """KIND-03 / D-09: a leaked ## Гайд heading is deleted then persist proceeds."""
    persist = _persist()
    asyncio.run(
        run_ingest_pipeline(
            URL,
            TemplateKind.LECTURE,
            captions=FakeTranscriptProvider(result=_transcript()),
            metadata_provider=FakeVideoMetadataProvider(result=_metadata()),
            article=FakeArticleGenerator(
                result=ArticleDraft.model_validate(
                    {"title": "T", "dek": "D", "body_markdown": body}
                )
            ),
            persist=persist,
            classifier=_classifier(),
        )
    )

    assert persist.calls, "furniture-only Гайд must strip then persist, not fail ingest"
    stored = persist.calls[0]
    assert "Гайд" not in stored.body_markdown
    assert stored.body_markdown.strip() != ""


def test_ingest_pipeline_does_not_wire_pass2_extras() -> None:
    from ingestion_service.application.use_cases import ingest_pipeline as mod

    source = inspect.getsource(mod)
    for ident in (
        "ArticleEnricher",
        "WebSearch",
        "PageExtract",
        "cheat_sheet",
        "tavily",
        "personal_kb",
        "UrlLiveness",
    ):
        assert ident not in source

