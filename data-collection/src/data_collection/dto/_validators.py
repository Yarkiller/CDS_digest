"""Private shared DTO field validators — not part of public API."""


def strip_non_blank(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("must not be blank")
    return cleaned
