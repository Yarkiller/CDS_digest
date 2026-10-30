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
# Exact ATX heading «Гайд» (KIND-03). IGNORECASE so a leaked lowercase «гайд»
# cannot survive (RESEARCH A3). D-12 “exact” means do not match Guide / How-to.
_GUIDE_HEADING_RE = re.compile(
    r"^#{2,6}[ \t]+Гайд[ \t]*$", re.IGNORECASE | re.MULTILINE
)
_GUIDE_PLACEHOLDER = "ссылки скоро появятся"
_GUIDE_PLACEHOLDER_RE = re.compile(re.escape(_GUIDE_PLACEHOLDER), re.IGNORECASE)
# KIND-03: an emptied body must still satisfy ArticleDraft min_length=1.
_EMPTY_BODY_STUB = "."
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


def strip_guide_section(body_markdown: str) -> str:
    """Drop a leaked `## Гайд` extras block and the honest-absence substring.

    Removes every ATX `Гайд` heading and its content up to the next h1/h2
    heading, then deletes every occurrence of «ссылки скоро появятся».
    Leaves the text untouched when no such heading exists (in-prose «гайд»
    and D-12 talk titles survive). Never raises — a leaked heading is
    deleted, not rejected. If stripping would empty the body, keep a
    non-empty stub so ArticleDraft min_length=1 still validates.
    """
    cleaned = body_markdown
    while True:
        match = _GUIDE_HEADING_RE.search(cleaned)
        if match is None:
            break
        tail = cleaned[match.end() :]
        next_heading = _NEXT_TOP_HEADING_RE.search(tail)
        if next_heading is None:
            stripped = cleaned[: match.start()]
        else:
            stripped = cleaned[: match.start()] + tail[next_heading.start() :]
        if stripped == cleaned:
            break
        cleaned = stripped
    cleaned = _GUIDE_PLACEHOLDER_RE.sub("", cleaned).strip()
    return cleaned if cleaned else _EMPTY_BODY_STUB
