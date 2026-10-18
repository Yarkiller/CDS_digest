"""Scripted success + call-spy fakes for ingestion ports (D-15, D-16, D-17, D-26)."""

from __future__ import annotations

import asyncio
from typing import TypedDict

from data_collection.dto.article_draft import ArticleDraft
from data_collection.dto.template_kind import TemplateKind
from data_collection.dto.transcript import Transcript
from data_collection.dto.video_metadata import VideoMetadata
from data_collection.errors.article import ArticleError
from data_collection.errors.captions import CaptionsError
from data_collection.errors.metadata import MetadataError


class ArticleGeneratorCall(TypedDict):
    transcript: Transcript
    template: TemplateKind


class FakeTranscriptProvider:
    def __init__(
        self,
        result: Transcript,
        failures: dict[str, CaptionsError] | None = None,
    ) -> None:
        self._result = result
        self._failures = failures or {}
        self.calls: list[str] = []

    async def get(self, video_id: str) -> Transcript:
        self.calls.append(video_id)
        if video_id in self._failures:
            raise self._failures[video_id]
        await asyncio.sleep(0)
        return self._result


class FakeVideoMetadataProvider:
    def __init__(
        self,
        result: VideoMetadata,
        failures: dict[str, MetadataError] | None = None,
    ) -> None:
        self._result = result
        self._failures = failures or {}
        self.calls: list[str] = []

    async def get(self, video_id: str) -> VideoMetadata:
        self.calls.append(video_id)
        if video_id in self._failures:
            raise self._failures[video_id]
        await asyncio.sleep(0)
        return self._result


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
        await asyncio.sleep(0)
        return self._result
