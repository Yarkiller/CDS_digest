"""score_factors honesty helper — ADMIN-05 / ADUX-06 / D-14 (≥2 labels or empty).

Named matrix: 0 factors · 1 readable · 2+ readable · whitespace-only (D-14).
"""

from __future__ import annotations

from backend.domain.shortlist import honest_factor_labels


def test_honest_factor_labels_zero_factors_returns_empty() -> None:
    """D-14 matrix: 0 factors → no labels (FE shows D-15 empty copy)."""
    assert honest_factor_labels({}) == []
    assert honest_factor_labels(None) == []
    assert honest_factor_labels({"factors": []}) == []


def test_honest_factor_labels_one_readable_label_returns_empty() -> None:
    """D-14 matrix: 1 readable label is insufficient — honesty empty."""
    assert honest_factor_labels({"factors": [{"label": "Только один"}]}) == []
    assert honest_factor_labels({"Единственный": 1.0}) == []


def test_honest_factor_labels_two_or_more_readable_returns_labels() -> None:
    """D-14 matrix: ≥2 readable labels returned as-is (never fabricated)."""
    labels = honest_factor_labels(
        {
            "factors": [
                {"label": "Релевантность"},
                {"label": "Свежесть"},
            ]
        }
    )
    assert labels == ["Релевантность", "Свежесть"]


def test_honest_factor_labels_whitespace_only_returns_empty() -> None:
    """D-14 matrix: whitespace-only labels/keys do not count as readable."""
    assert honest_factor_labels({"factors": [{"label": ""}, {"label": "  "}]}) == []
    assert honest_factor_labels({"factors": [{"label": "\t"}, {"label": "\n"}]}) == []
    assert honest_factor_labels({"  ": 0.5, "\t": 0.4}) == []


def test_honest_factor_labels_returns_labels_from_flat_map_keys() -> None:
    labels = honest_factor_labels({"Релевантность": 0.8, "Свежесть": 0.6})
    assert labels == ["Релевантность", "Свежесть"]


def test_honest_factor_labels_falls_back_to_flat_keys_when_factors_list_empty() -> None:
    """WR-02: empty ``factors: []`` must not shadow ≥2 readable flat keys (demo seed honesty)."""
    labels = honest_factor_labels(
        {
            "релевантность теме недели": 0.9,
            "качество источников": 0.85,
            "factors": [],
        }
    )
    assert labels == ["релевантность теме недели", "качество источников"]


def test_honest_factor_labels_falls_back_to_flat_keys_when_structured_labels_blank() -> None:
    """WR-02: non-empty factors with only blank/non-dict entries must fall through to flat keys."""
    labels = honest_factor_labels(
        {
            "factors": [{"label": "  "}, "x"],
            "Релевантность": 0.8,
            "Свежесть": 0.6,
        }
    )
    assert labels == ["Релевантность", "Свежесть"]


def test_honest_factor_labels_ignores_blank_labels_in_list() -> None:
    labels = honest_factor_labels(
        {
            "factors": [
                {"label": "  "},
                {"label": "A"},
                {"label": "B"},
            ]
        }
    )
    assert labels == ["A", "B"]
