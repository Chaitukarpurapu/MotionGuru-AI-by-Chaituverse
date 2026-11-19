"""MotionGuru CLI: analyze -> approve proposals -> render."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from .core import kept_intervals, make_silence_proposals, validate_proposals
from .media import detect_silences, probe, render_intervals


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("The decisions document must be a JSON object")
    validate_proposals(data)
    return data


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def cmd_analyze(args) -> None:
    source = Path(args.input).resolve()
    meta = probe(source)
    silences = detect_silences(source, meta["duration"], noise_db=args.noise_db,
                              min_duration=args.min_silence) if meta["has_audio"] else []
    proposals = make_silence_proposals(silences, meta["duration"])
    project = {
        "schema_version": 1,
        "source": str(source),
        "duration": round(meta["duration"], 6),
        "has_audio": meta["has_audio"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "proposals": proposals,
    }
    save_json(Path(args.output), project)
    print(f"Video: {source.name} ({meta['duration']:.2f}s)")
    print(f"Proposed cuts: {len(proposals)} (all pending approval)")
    print(f"Review: motionguru review \"{args.output}\"")


def cmd_review(args) -> None:
    path = Path(args.decisions)
    project = load_json(path)
    for proposal in project["proposals"]:
        print(f"\n{proposal['id']}: {proposal['start']:.2f}–{proposal['end']:.2f}s — {proposal['reason']}")
        while True:
            decision = input("Cut this segment? [c]ut / [k]eep / [s]kip: ").strip().lower()
            if decision in ("c", "k", "s"):
                break
            print("Enter c, k or s.")
        if decision != "s":
            proposal["decision"] = "cut" if decision == "c" else "keep"
            save_json(path, project)
    pending = sum(p["decision"] == "pending" for p in project["proposals"])
    print(f"Saved decisions: {path}. Pending: {pending}")


def cmd_render(args) -> None:
    source = Path(args.input).resolve()
    output = Path(args.output).resolve()
    document = load_json(Path(args.decisions))
    if source != Path(document["source"]).resolve():
        raise ValueError("Source video differs from analyzed source; rerun analyze")
    actual = probe(source)
    if abs(actual["duration"] - document["duration"]) > 0.05:
        raise ValueError("Source duration has changed; rerun analyze")
    intervals = kept_intervals(document)
    render_intervals(source, output, intervals, actual["has_audio"])
    print(f"Saved edited MP4 to {output}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="motionguru", description="MotionGuru AI — smart cuts v0.1")
    sub = parser.add_subparsers(dest="command", required=True)
    analyze = sub.add_parser("analyze", help="Find quiet regions and propose cuts")
    analyze.add_argument("input")
    analyze.add_argument("--output", required=True)
    analyze.add_argument("--noise-db", type=int, default=-35)
    analyze.add_argument("--min-silence", type=float, default=0.65)
    review = sub.add_parser("review", help="Approve or keep suggested cuts")
    review.add_argument("decisions")
    render = sub.add_parser("render", help="Render approved edit into a new MP4")
    render.add_argument("input")
    render.add_argument("--decisions", required=True)
    render.add_argument("--output", required=True)
    analyze.set_defaults(func=cmd_analyze)
    review.set_defaults(func=cmd_review)
    render.set_defaults(func=cmd_render)
    args = parser.parse_args(argv)
    try:
        args.func(args)
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"MotionGuru error: {exc}", file=sys.stderr)
        return 1
    except __import__("subprocess").CalledProcessError as exc:
        print(f"FFmpeg failed (exit {exc.returncode}): {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
