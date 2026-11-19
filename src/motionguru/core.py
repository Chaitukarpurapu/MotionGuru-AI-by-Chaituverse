"""Pure, testable time-interval and decision logic for non-destructive cuts."""

from __future__ import annotations

from math import isfinite


def validate_proposals(project: dict) -> None:
    duration = project.get("duration")
    if not isinstance(duration, (int, float)) or not isfinite(duration) or duration <= 0:
        raise ValueError("Project duration must be a positive finite number")
    proposals = project.get("proposals")
    if not isinstance(proposals, list):
        raise ValueError("Project proposals must be an array")
    last_end = 0.0
    ids: set[str] = set()
    for item in proposals:
        if not isinstance(item, dict):
            raise ValueError("Invalid proposal")
        start, end = item.get("start"), item.get("end")
        if (not isinstance(start, (int, float)) or not isinstance(end, (int, float))
                or not isfinite(start) or not isfinite(end)
                or start < 0 or end > duration + 1e-4 or end <= start):
            raise ValueError(f"Invalid proposed cut time range: {item!r}")
        if start < last_end - 1e-6:
            raise ValueError("Proposals must be sorted and non-overlapping")
        last_end = float(end)
        decision = item.get("decision", "pending")
        if decision not in ("pending", "cut", "keep"):
            raise ValueError(f"Invalid cut decision: {decision!r}")
        key = item.get("id")
        if not isinstance(key, str) or not key or key in ids:
            raise ValueError("Each proposal needs a distinct nonempty ID")
        ids.add(key)


def kept_intervals(project: dict, *, min_length: float = 0.02) -> list[tuple[float, float]]:
    """Return timeline segments to retain; all proposals require explicit review."""
    validate_proposals(project)
    proposals = project["proposals"]
    if any(p.get("decision", "pending") == "pending" for p in proposals):
        raise ValueError("Unreviewed cuts remain. Run 'motionguru review' first.")
    duration = float(project["duration"])
    kept: list[tuple[float, float]] = []
    cursor = 0.0
    for p in proposals:
        if p["decision"] != "cut":
            continue
        start, end = float(p["start"]), float(p["end"])
        if start - cursor >= min_length:
            kept.append((cursor, start))
        cursor = end
    if duration - cursor >= min_length:
        kept.append((cursor, duration))
    if not kept:
        raise ValueError("All footage would be removed; refusing to render empty output.")
    return kept


def make_silence_proposals(intervals: list[tuple[float, float]],
                           duration: float, *, min_cut: float = 0.5,
                           edge_margin: float = 0.15) -> list[dict]:
    """Create conservative, non-overlapping cut suggestions from silence detections."""
    proposed = []
    for left, right in sorted(intervals):
        left = max(edge_margin, float(left))
        right = min(float(duration) - edge_margin, float(right))
        if right - left < min_cut:
            continue
        if proposed and left < proposed[-1]["end"]:
            proposed[-1]["end"] = max(proposed[-1]["end"], right)
            continue
        proposed.append({
            "id": f"cut-{len(proposed)+1:03d}",
            "start": round(left, 3),
            "end": round(right, 3),
            "reason": "Detected quiet audio; review before deleting",
            "decision": "pending",
        })
    return proposed
