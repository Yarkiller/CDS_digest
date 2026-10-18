"""TemplateKind closed set for lecture/podcast prompts (D-10)."""

from enum import Enum


class TemplateKind(str, Enum):
    LECTURE = "lecture"
    PODCAST = "podcast"
