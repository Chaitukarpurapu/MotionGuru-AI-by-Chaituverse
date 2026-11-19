"""MotionGuru AI CLI: smart cuts, motion graphics, captions and audio."""

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
        "schema_version": 1, "source": str(source),
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
        if proposal["decision"] != "pending":
            continue
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


def cmd_motion(args):
    from .motion import load_project, render_motion
    project = load_project(Path(args.project))
    result = render_motion(project, Path(args.output), preview=Path(args.preview) if args.preview else None)
    print(json.dumps(result,indent=2))


def cmd_captions(args):
    from .captions import ass_from_segments, parse_srt, srt_from_segments, transcribe, burn_ass
    if args.caption_command == "transcribe":
        words = transcribe(Path(args.input), model_name=args.model, language=args.language)
        target=Path(args.output)
        if target.suffix.lower()==".ass":
            target.write_text(ass_from_segments(words,style=args.style,width=args.width,height=args.height),
                              encoding="utf-8")
        else:
            target.write_text(srt_from_segments(words),encoding="utf-8")
        print(f"Created {len(words)} timed caption segments: {target}")
    elif args.caption_command == "style":
        segments = parse_srt(Path(args.input).read_text(encoding="utf-8-sig"))
        Path(args.output).write_text(
            ass_from_segments(segments,style=args.style,width=args.width,height=args.height),
            encoding="utf-8")
        print(f"Created {len(segments)} styled captions: {args.output}")
    elif args.caption_command == "burn":
        burn_ass(Path(args.input),Path(args.captions),Path(args.output))
        print(f"Saved captioned video: {args.output}")


def cmd_sfx(args):
    from .audio import generate_sfx
    generate_sfx(args.kind,Path(args.output),duration=args.duration)
    print(f"Created original {args.kind} SFX: {args.output}")


def cmd_mix(args):
    from .audio import mix_audio
    mix_audio(Path(args.input), Path(args.output),
              music=Path(args.music) if args.music else None,
              sfx=Path(args.sfx) if args.sfx else None,
              music_volume=args.music_volume,sfx_volume=args.sfx_volume)
    print(f"Exported audio mix: {args.output}")


def cmd_studio(args):
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
    from functools import partial
    from .studio import asset_folder
    directory=asset_folder()
    handler=partial(SimpleHTTPRequestHandler,directory=str(directory))
    print(f"MotionGuru Studio: http://127.0.0.1:{args.port}")
    print("Use the browser to load and edit a scene JSON file; rendering uses the CLI.")
    server=ThreadingHTTPServer(("127.0.0.1",args.port),handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="motionguru",description="MotionGuru AI — local-first video toolkit")
    sub = parser.add_subparsers(dest="command",required=True)

    analyze=sub.add_parser("analyze",help="Propose silence cuts")
    analyze.add_argument("input")
    analyze.add_argument("--output",required=True)
    analyze.add_argument("--noise-db",type=int,default=-35)
    analyze.add_argument("--min-silence",type=float,default=0.65)
    analyze.set_defaults(func=cmd_analyze)

    review=sub.add_parser("review",help="Approve or keep proposed cuts")
    review.add_argument("decisions")
    review.set_defaults(func=cmd_review)

    render=sub.add_parser("render",help="Export manually approved edits")
    render.add_argument("input")
    render.add_argument("--decisions",required=True)
    render.add_argument("--output",required=True)
    render.set_defaults(func=cmd_render)

    motion=sub.add_parser("motion",help="Render JSON motion scenes as MP4 or PNG")
    motion.add_argument("project")
    motion.add_argument("--output",required=True)
    motion.add_argument("--preview",help="Write one PNG frame instead of rendering video")
    motion.set_defaults(func=cmd_motion)

    captions=sub.add_parser("captions",help="Transcribe, style or burn subtitles")
    caption_sub=captions.add_subparsers(dest="caption_command",required=True)

    transcribe=caption_sub.add_parser("transcribe")
    transcribe.add_argument("input")
    transcribe.add_argument("--output",required=True,help=".srt or .ass")
    transcribe.add_argument("--model",default="small")
    transcribe.add_argument("--language",default=None)
    transcribe.add_argument("--style",default="editorial")
    transcribe.add_argument("--width",type=int,default=1080)
    transcribe.add_argument("--height",type=int,default=1920)
    transcribe.set_defaults(func=cmd_captions)

    style=caption_sub.add_parser("style")
    style.add_argument("input",help="Source .srt")
    style.add_argument("--output",required=True,help="Destination .ass")
    style.add_argument("--style",default="editorial")
    style.add_argument("--width",type=int,default=1080)
    style.add_argument("--height",type=int,default=1920)
    style.set_defaults(func=cmd_captions)

    burn=caption_sub.add_parser("burn")
    burn.add_argument("input",help="Input MP4")
    burn.add_argument("--captions",required=True,help="Styled .ass")
    burn.add_argument("--output",required=True)
    burn.set_defaults(func=cmd_captions)

    sfx=sub.add_parser("sfx",help="Synthesize original SFX WAV")
    sfx.add_argument("kind",choices=["impact","whoosh","riser","pop","click","sweep"])
    sfx.add_argument("--duration",type=float,default=0.65)
    sfx.add_argument("--output",required=True)
    sfx.set_defaults(func=cmd_sfx)

    mix=sub.add_parser("mix",help="Mix voice, music and SFX into a video")
    mix.add_argument("input")
    mix.add_argument("--music")
    mix.add_argument("--sfx")
    mix.add_argument("--music-volume",type=float,default=0.2)
    mix.add_argument("--sfx-volume",type=float,default=0.6)
    mix.add_argument("--output",required=True)
    mix.set_defaults(func=cmd_mix)

    studio=sub.add_parser("studio",help="Launch local scene preview studio")
    studio.add_argument("--port",type=int,default=8765)
    studio.set_defaults(func=cmd_studio)

    args=parser.parse_args(argv)
    try:
        args.func(args)
        return 0
    except (OSError,ValueError,RuntimeError) as exc:
        print(f"MotionGuru error: {exc}",file=sys.stderr)
        return 1
    except __import__("subprocess").CalledProcessError as exc:
        print(f"FFmpeg failed (exit {exc.returncode}): {exc}",file=sys.stderr)
        return 1


if __name__=="__main__":
    raise SystemExit(main())
