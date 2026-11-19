"""FFmpeg/ffprobe adapters. All inputs use argument arrays, never a shell."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path


def require_tools() -> None:
    missing = [x for x in ("ffmpeg", "ffprobe") if shutil.which(x) is None]
    if missing:
        raise RuntimeError(f"Missing {' and '.join(missing)} on PATH. Install FFmpeg first.")


def probe(path: Path) -> dict:
    require_tools()
    if not path.is_file():
        raise FileNotFoundError(f"Video not found: {path}")
    proc = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate",
        "-of", "json", str(path)
    ], capture_output=True, text=True, check=True)
    data = json.loads(proc.stdout)
    duration = float(data.get("format", {}).get("duration", 0))
    if duration <= 0:
        raise ValueError("Could not read a valid positive video duration")
    if not any(s.get("codec_type") == "video" for s in data.get("streams", [])):
        raise ValueError("Source has no video stream")
    return {
        "duration": duration,
        "streams": data.get("streams", []),
        "has_audio": any(s.get("codec_type") == "audio" for s in data.get("streams", [])),
    }


def detect_silences(path: Path, duration: float, *, noise_db: int = -35,
                    min_duration: float = 0.65) -> list[tuple[float, float]]:
    if not (-90 <= noise_db <= -5):
        raise ValueError("noise_db must be between -90 and -5 dB")
    if not (0.1 <= min_duration <= 30):
        raise ValueError("min_duration must be between 0.1 and 30 seconds")
    proc = subprocess.run([
        "ffmpeg", "-hide_banner", "-nostdin", "-i", str(path),
        "-af", f"silencedetect=noise={noise_db}dB:d={min_duration}",
        "-vn", "-f", "null", "-"
    ], capture_output=True, text=True, check=True)
    events: list[tuple[str, float]] = []
    for line in proc.stderr.splitlines():
        start = re.search(r"silence_start:\s*(-?\d+(?:\.\d+)?)", line)
        end = re.search(r"silence_end:\s*(-?\d+(?:\.\d+)?)", line)
        if start:
            events.append(("start", float(start.group(1))))
        if end:
            events.append(("end", float(end.group(1))))
    silences = []
    active: float | None = None
    for kind, time in events:
        if kind == "start":
            active = max(0.0, time)
        elif active is not None:
            silences.append((active, min(duration, time)))
            active = None
    if active is not None:
        silences.append((active, duration))
    return silences


def render_intervals(source: Path, output: Path, intervals: list[tuple[float, float]],
                     has_audio: bool) -> None:
    require_tools()
    if source.resolve() == output.resolve():
        raise ValueError("Output cannot overwrite the original source video")
    output.parent.mkdir(parents=True, exist_ok=True)
    pieces: list[str] = []
    mapping: list[str] = []
    for idx, (start, end) in enumerate(intervals):
        if end <= start:
            raise ValueError("Invalid kept interval")
        pieces.append(
            f"[0:v:0]trim=start={start:.6f}:end={end:.6f},setpts=PTS-STARTPTS[v{idx}]"
        )
        if has_audio:
            pieces.append(
                f"[0:a:0]atrim=start={start:.6f}:end={end:.6f},asetpts=PTS-STARTPTS[a{idx}]"
            )
        mapping.append(f"[v{idx}]" + (f"[a{idx}]" if has_audio else ""))
    if has_audio:
        filter_complex = ";".join(pieces + [
            "".join(mapping) + f"concat=n={len(intervals)}:v=1:a=1[vout][aout]"
        ])
    else:
        filter_complex = ";".join(pieces + [
            "".join(mapping) + f"concat=n={len(intervals)}:v=1:a=0[vout]"
        ])
    cmd = ["ffmpeg", "-hide_banner", "-nostdin", "-y", "-i", str(source),
           "-filter_complex", filter_complex, "-map", "[vout]"]
    if has_audio:
        cmd += ["-map", "[aout]", "-c:a", "aac", "-b:a", "192k"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(output)]
    subprocess.run(cmd, check=True)
