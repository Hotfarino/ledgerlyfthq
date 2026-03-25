from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List

from models.schemas import Phase0PainPoint, Phase0Report
from services.repository import repository

PAIN_POINT_LABELS = {
    "selection": "Selection",
    "slippage": "Slippage",
    "router_lag": "Router Lag",
    "venue_lag": "Venue Lag",
    "fill_quality": "Fill Quality",
}

SELECTION_FLAGS = {"missing_date", "missing_amount", "invalid_date", "blank_description_payee", "malformed_row"}
SLIPPAGE_FLAGS = {"invalid_amount", "ambiguous_debit_credit", "inconsistent_sign"}
FILL_QUALITY_FLAGS = {"suspicious_duplicate", "uncategorized_transaction", "possible_transfer_pair", "amount_outlier"}


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def build_phase0_report(lookback_days: int = 60) -> Phase0Report:
    now = datetime.utcnow()
    cutoff = now - timedelta(days=lookback_days)

    pain_counts: Dict[str, int] = {key: 0 for key in PAIN_POINT_LABELS.keys()}
    jobs = [job for job in repository.list_jobs() if (_parse_ts(job.get("uploaded_at")) or datetime.min) >= cutoff]

    rows_analyzed = 0
    for job in jobs:
        job_id = job["job_id"]
        summary = job.get("summary", {})
        rows_analyzed += int(summary.get("total_rows_imported", job.get("row_count", 0)) or 0)

        exceptions = repository.list_exceptions(job_id)
        for item in exceptions:
            flag = item.flag_type
            if flag in SELECTION_FLAGS:
                pain_counts["selection"] += 1
            elif flag in SLIPPAGE_FLAGS:
                pain_counts["slippage"] += 1
            elif flag in FILL_QUALITY_FLAGS:
                pain_counts["fill_quality"] += 1

        # Re-runs suggest operator friction in pipeline routing and mapping.
        audits = repository.list_audit_entries(job_id)
        pain_counts["router_lag"] += sum(1 for entry in audits if entry.action in {"cleanup_rerun", "apply_category_rules"})

        # Export lag from upload to first export is treated as venue lag signal.
        uploaded_at = _parse_ts(job.get("uploaded_at"))
        exported_at = _parse_ts(job.get("last_export_at"))
        if uploaded_at and exported_at:
            lag_hours = (exported_at - uploaded_at).total_seconds() / 3600
            if lag_hours > 24:
                pain_counts["venue_lag"] += 1
        elif uploaded_at and (now - uploaded_at).total_seconds() > 24 * 3600:
            pain_counts["venue_lag"] += 1

        pain_counts["fill_quality"] += len(repository.list_duplicates(job_id))

    signals_total = sum(pain_counts.values())
    top_key = max(pain_counts, key=lambda key: pain_counts[key]) if signals_total else "selection"

    pain_points: List[Phase0PainPoint] = []
    for key, label in PAIN_POINT_LABELS.items():
        count = pain_counts[key]
        percent = round((count / signals_total) * 100, 2) if signals_total else 0.0
        pain_points.append(
            Phase0PainPoint(
                key=key,
                label=label,
                count=count,
                percent_of_signals=percent,
            )
        )

    notes = [
        f"Using actual local job history from the last {lookback_days} days.",
        "Default assumption is isolated execution mode; shared adapter mode must be explicitly enabled.",
    ]
    if not jobs:
        notes.append("No jobs were found in the selected lookback window.")

    return Phase0Report(
        lookback_days=lookback_days,
        generated_at=now,
        jobs_analyzed=len(jobs),
        rows_analyzed=rows_analyzed,
        signals_total=signals_total,
        top_pain_area=PAIN_POINT_LABELS[top_key],
        pain_points=pain_points,
        notes=notes,
    )
