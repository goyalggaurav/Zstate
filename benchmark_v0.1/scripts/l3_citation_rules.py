"""L3 citation rule helpers — archetype baselines + per-task gold_path overrides (P3-29)."""

from __future__ import annotations

import re
from typing import Any

ARCHETYPE_L3_BASELINE: dict[str, dict[str, Any]] = {
    "F_exact": {
        "distinct_snippets_required": True,
        "max_snippet_chars": 140,
        "forbid_note_number_only": True,
        "require_numeric_in_snippet": True,
    },
    "F_adjustment": {
        "distinct_snippets_required": True,
        "max_snippet_chars": 140,
        "forbid_note_number_only": True,
        "require_numeric_in_snippet": True,
    },
    "F_guidance_drift": {
        "distinct_snippets_required": True,
        "max_snippet_chars": 160,
        "forbid_note_number_only": True,
        "require_numeric_in_snippet": True,
    },
    "M_organic": {
        "distinct_snippets_required": True,
        "max_snippet_chars": 140,
        "forbid_note_number_only": True,
        "require_numeric_in_snippet": True,
    },
}

NOTE_ONLY_RE = re.compile(r"^note\s+\d+\.?$", re.IGNORECASE)


def merge_l3_rules(archetype: str, gold_rules: dict[str, Any] | None) -> dict[str, Any]:
    merged = dict(ARCHETYPE_L3_BASELINE.get(archetype, {}))
    merged.update(gold_rules or {})
    return merged


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def is_note_number_only(snippet: str) -> bool:
    return bool(NOTE_ONLY_RE.match(normalize(snippet)))


def numeric_forms(value: int | float) -> list[str]:
    forms: list[str] = []
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    if isinstance(value, int):
        forms.extend([str(value), f"{value:,}"])
        if value < 0:
            abs_v = abs(value)
            forms.extend([f"({abs_v:,})", f"({abs_v})"])
    elif isinstance(value, float):
        forms.extend([str(value), f"{value:.1f}", f"{value:.1f}".rstrip("0").rstrip(".")])
        if value < 0:
            forms.append(f"({abs(value):.0f})")
            forms.append(f"({abs(value):.1f})")
        if abs(value) < 100:
            for prec in (0, 1):
                mag = abs(value)
                txt = f"{mag:.{prec}f}".rstrip("0").rstrip(".") if prec else f"{mag:.0f}"
                forms.append(f"{value:.1f}%".rstrip("0").rstrip("."))
                forms.append(f"({txt})%")
                if value < 0:
                    forms.append(f"({txt})")
    return forms


def numeric_optional(metric_id: str, l3_rules: dict) -> bool:
    optional = set(l3_rules.get("numeric_optional_metrics") or [])
    optional.update({"segment_sum", "reconciling_item_amount"})
    return metric_id in optional


def numeric_in_snippet(value: Any, snippet: str) -> bool:
    if value is None or isinstance(value, bool):
        return True
    if not isinstance(value, (int, float)):
        return True
    compact = normalize(snippet).replace(",", "").replace(" ", "")
    for form in numeric_forms(value):
        token = form.replace(",", "").replace(" ", "")
        if token and token in compact:
            return True
    return False


def anchor_ok(
    snippet: str,
    anchor: dict[str, Any],
    *,
    section_slug: str | None,
) -> tuple[bool, str | None]:
    if section_slug and anchor.get("section_slug") and anchor["section_slug"] != section_slug:
        return True, None
    norm = normalize(snippet)
    norm_lower = norm.lower()
    if anchor.get("row_label"):
        label = str(anchor["row_label"])
        if label.lower() not in norm_lower:
            return False, "missing_row_label"
    if anchor.get("column_header"):
        header = str(anchor["column_header"])
        if header.lower() not in norm_lower:
            return False, "missing_column_header"
    return True, None
