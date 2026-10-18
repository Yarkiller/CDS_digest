"""Body normalisation for internal LLM drafts.

`lecture.md` / `podcast.md` end with a `## Аудитория` heading whose content is an
*instruction* to emit a JSON array of roles. The authoritative role contract is
the separate JSON `roles` key, so that heading is prompt scaffolding rather than
article content — yet models routinely emit it inside `body_markdown` too, either
as the raw answer (`["employee", "analyst", "ds"]`) or by echoing the instruction
verbatim. Both variants were observed on live materials. Strip the section so the
reader-facing body stays clean.
"""

from __future__ import annotations

import re

# A level-2+ ATX heading whose whole text is exactly "Аудитория".
_AUDIENCE_HEADING_RE = re.compile(
    r"^#{2,6}[ \t]+Аудитория[ \t]*$", re.IGNORECASE | re.MULTILINE
)
# The end of the scaffolding block: the next top-level (h1/h2) heading, if any.
_NEXT_TOP_HEADING_RE = re.compile(r"^#{1,2}[ \t]+\S", re.MULTILINE)


def strip_audience_section(body_markdown: str) -> str:
    """Drop the trailing `## Аудитория` prompt-scaffolding block, if present.

    Removes the heading and its content up to the next h1/h2 heading (normally
    end-of-body, since the templates place it last). Leaves the text untouched
    when no such heading exists, so an in-prose mention of "аудитория" survives.
    """
    match = _AUDIENCE_HEADING_RE.search(body_markdown)
    if match is None:
        return body_markdown

    tail = body_markdown[match.end():]
    next_heading = _NEXT_TOP_HEADING_RE.search(tail)
    if next_heading is None:
        cleaned = body_markdown[: match.start()]
    else:
        cleaned = body_markdown[: match.start()] + tail[next_heading.start():]
    return cleaned.strip()
