"""Public API for data-collection ingestion contracts (D-01, D-04, D-21)."""

from data_collection.dto.material_draft import MaterialDraft
from data_collection.dto.template_kind import TemplateKind
from data_collection.dto.transcript import Transcript
from data_collection.dto.video_metadata import VideoMetadata
from data_collection.dto.video_ref import FeedListing, VideoRef
from data_collection.ports.article_generator import ArticleGenerator
from data_collection.ports.transcript_provider import TranscriptProvider
from data_collection.ports.video_list_provider import VideoListProvider
from data_collection.ports.video_metadata_provider import VideoMetadataProvider

__all__ = [
    "Transcript",
    "VideoMetadata",
    "MaterialDraft",
    "TemplateKind",
    "TranscriptProvider",
    "ArticleGenerator",
    "VideoMetadataProvider",
    "VideoRef",
    "FeedListing",
    "VideoListProvider",
]
