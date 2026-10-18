"""Ports package for data-collection ingestion contracts."""

from data_collection.ports.article_generator import ArticleGenerator
from data_collection.ports.transcript_provider import TranscriptProvider
from data_collection.ports.video_list_provider import VideoListProvider
from data_collection.ports.video_metadata_provider import VideoMetadataProvider

__all__ = [
    "ArticleGenerator",
    "TranscriptProvider",
    "VideoMetadataProvider",
    "VideoListProvider",
]
