from __future__ import annotations

from typing import List

from models.schemas import CategoryRule, ConfidenceLevel, TransactionRow


def _score_confidence(rule_confidence: ConfidenceLevel, match_strength: float) -> ConfidenceLevel:
    if match_strength > 0.9:
        return ConfidenceLevel.HIGH
    if match_strength > 0.7:
        return ConfidenceLevel.MEDIUM
    return rule_confidence


def apply_category_rules(rows: List[TransactionRow], rules: List[CategoryRule], preview_only: bool = False) -> List[TransactionRow]:
    active_rules = [r for r in rules if r.active]
    for row in rows:
        best_rule = None
        best_strength = 0.0

        for rule in active_rules:
            source = str(row.cleaned_values.get(rule.target_field, "") or "")
            contains = rule.contains_text.lower().strip()
            source_lower = source.lower()
            if not contains or contains not in source_lower:
                continue

            strength = len(contains) / max(len(source_lower), 1)
            if strength > best_strength:
                best_strength = strength
                best_rule = rule

        if best_rule:
            row.category_suggestion = best_rule.suggested_category
            row.category_confidence = _score_confidence(best_rule.confidence, best_strength)
            if not preview_only and not row.cleaned_values.get("category"):
                row.cleaned_values["category"] = best_rule.suggested_category
                row.flags = [f for f in row.flags if f != "uncategorized_transaction"]

    return rows
