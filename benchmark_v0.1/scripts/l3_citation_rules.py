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

METRIC_UNIT_SUFFIX: dict[str, str] = {
    "_usd_m": "USD_millions",
    "_pct": "percent",
    "_months": "months",
}

NOTE_ONLY_RE = re.compile(r"^note\s+\d+\.?$", re.IGNORECASE)

WORD_NUMBERS: dict[int, str] = {
    1: "one",
    2: "two",
    3: "three",
    4: "four",
    5: "five",
    6: "six",
    7: "seven",
    8: "eight",
    9: "nine",
    10: "ten",
    12: "twelve",
}


def merge_l3_rules(archetype: str, gold_rules: dict[str, Any] | None) -> dict[str, Any]:
    merged = dict(ARCHETYPE_L3_BASELINE.get(archetype, {}))
    gold_rules = dict(gold_rules or {})
    computed = gold_rules.pop("computed_citations", None) or {}
    merged.update(gold_rules)
    optional = set(merged.get("numeric_optional_metrics") or [])
    for metric_id, policy in computed.items():
        if policy.get("numeric_optional"):
            optional.add(metric_id)
    merged["numeric_optional_metrics"] = sorted(optional)
    merged["_computed_citations"] = computed
    return merged


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def is_note_number_only(snippet: str) -> bool:
    return bool(NOTE_ONLY_RE.match(normalize(snippet)))


def infer_metric_unit(metric_id: str, metric_units: dict[str, str] | None = None) -> str | None:
    if metric_units and metric_id in metric_units:
        return metric_units[metric_id]
    if metric_id.endswith("_usd_m"):
        return "USD_millions"
    if metric_id.endswith("_pct"):
        return "percent"
    if metric_id.endswith("_months"):
        return "months"
    if metric_id in ("guidance_pace_under", "cc_growth_verified"):
        return "boolean"
    return None


def build_metric_units(gt_doc: dict | None, l3_rules: dict | None = None) -> dict[str, str]:
    units: dict[str, str] = {}
    if gt_doc:
        for section in ("extracted_values", "computed_values"):
            for item in gt_doc.get(section, []):
                mid = item.get("metric_id")
                unit = item.get("unit")
                if mid and unit:
                    units[mid] = str(unit)
    if l3_rules:
        units.update(l3_rules.get("metric_units") or {})
    return units


def numeric_forms(value: int | float, unit: str | None = None) -> list[str]:
    forms: list[str] = []
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    if isinstance(value, int):
        forms.extend([str(value), f"{value:,}"])
        if value < 0:
            abs_v = abs(value)
            forms.extend([f"({abs_v:,})", f"({abs_v})"])
        if unit in (None, "months"):
            word = WORD_NUMBERS.get(value)
            if word:
                forms.append(word)
        if unit in (None, "USD_millions") and value >= 1000:
            billions = value / 1000
            if billions == int(billions):
                b = int(billions)
                forms.extend([f"${b}B", f"{b}B", f"{b} billion"])
            else:
                forms.extend([f"${billions}B", f"{billions}B"])
    elif isinstance(value, float):
        if unit in (None, "percent"):
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
        else:
            forms.extend([str(value), f"{value:.1f}"])
    return forms


def numeric_optional(metric_id: str, l3_rules: dict) -> bool:
    optional = set(l3_rules.get("numeric_optional_metrics") or [])
    optional.update({"segment_sum", "reconciling_item_amount", "segment_net_revenues_sum", "segment_net_sales_sum"})
    return metric_id in optional


def numeric_in_snippet(value: Any, snippet: str, unit: str | None = None) -> bool:
    if value is None or isinstance(value, bool) or unit == "boolean":
        return True
    if not isinstance(value, (int, float)):
        return True
    norm = normalize(snippet)
    norm_lower = norm.lower()
    compact = norm.replace(",", "").replace(" ", "")
    for form in numeric_forms(value, unit=unit):
        token = form.replace(",", "").replace(" ", "")
        if token and token in compact:
            return True
        if token and token in norm_lower:
            return True
    if unit in (None, "USD_millions") and isinstance(value, int) and value >= 100:
        for match in re.finditer(r"\d{4,}", compact):
            filing_thousands = int(match.group())
            if round(filing_thousands / 1000) == value:
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
    norm_lower = normalize(snippet).lower()
    if anchor.get("row_label"):
        label = str(anchor["row_label"])
        if label.lower() not in norm_lower:
            return False, "missing_row_label"
    if anchor.get("column_header"):
        header = str(anchor["column_header"])
        if header.lower() not in norm_lower:
            return False, "missing_column_header"
    return True, None
