"""Real FFmpeg smoke tests for analyze -> human review -> render.

The fixture uses a short generated color video and an audio track containing
a precisely controlled 1-second silence. No stock videos or assets needed.
"""

import json
import shutil
import subprocess

import pytest

from motionguru.cli import main
from motionguru.media import probe


@pytest.mark.skipif(
    not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
    reason="FFmpeg and ffprobe required",
)
def test_full_smart_cut_workflow(tmp_path, monkeypatch, capsys):
    video = tmp_path / "source.mp4"
    decisions = tmp_path / "cuts.json"
    output = tmp_path / "edited.mp4"

    # Three 1-second audio segments: tone, silence, tone.
    # A silent audio segment is different from a missing audio stream.
    subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
            "-f", "lavfi", "-i", "color=c=blue:s=160x90:r=24:d=3",
            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=1",
            "-f", "lavfi", "-i",
            "anullsrc=channel_layout=mono:sample_rate=48000:d=1",
            "-f", "lavfi", "-i", "sine=frequency=550:sample_rate=48000:duration=1",
            "-filter_complex",
            "[1:a][2:a][3:a]concat=n=3:v=0:a=1[a]",
            "-map", "0:v:0", "-map", "[a]",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-shortest", str(video),
        ],
        capture_output=True, text=True, check=True,
    )

    original = probe(video)
    assert original["has_audio"]
    assert 2.8 < original["duration"] < 3.2

    assert main(["analyze", str(video), "--output", str(decisions),
                 "--min-silence", "0.5"]) == 0
    project = json.loads(decisions.read_text(encoding="utf-8"))
    assert project["proposals"], "The middle second of silence should be detected"
    assert any(0.8 <= p["start"] < 1.3 for p in project["proposals"])
    assert all(p["decision"] == "pending" for p in project["proposals"])

    # Export must not execute while any proposal remains pending.
    assert main(["render", str(video), "--decisions", str(decisions),
                 "--output", str(output)]) == 1
    assert not output.exists()

    # Explicit user review: approve each detected silence.
    monkeypatch.setattr("builtins.input", lambda _: "c")
    assert main(["review", str(decisions)]) == 0
    reviewed = json.loads(decisions.read_text(encoding="utf-8"))
    assert all(p["decision"] == "cut" for p in reviewed["proposals"])

    assert main(["render", str(video), "--decisions", str(decisions),
                 "--output", str(output)]) == 0
    rendered = probe(output)
    assert rendered["has_audio"]
    assert 1.5 < rendered["duration"] < 2.7
    assert video.exists(), "Original source must remain untouched"
    assert output.stat().st_size > 500


@pytest.mark.skipif(
    not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
    reason="FFmpeg and ffprobe required",
)
def test_kept_silence_preserves_original_duration(tmp_path, monkeypatch):
    source = tmp_path / "source.mp4"
    decisions = tmp_path / "cuts.json"
    output = tmp_path / "kept.mp4"
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
         "-f", "lavfi", "-i", "color=c=red:s=160x90:r=24:d=2",
         "-f", "lavfi", "-i", "anullsrc=channel_layout=mono:sample_rate=48000:d=2",
         "-c:v", "libx264", "-c:a", "aac", "-shortest", str(source)],
        capture_output=True, text=True, check=True,
    )
    assert main(["analyze", str(source), "--output", str(decisions),
                 "--min-silence", "0.5"]) == 0
    monkeypatch.setattr("builtins.input", lambda _: "k")
    assert main(["review", str(decisions)]) == 0
    assert main(["render", str(source), "--decisions", str(decisions),
                 "--output", str(output)]) == 0
    assert abs(probe(output)["duration"] - probe(source)["duration"]) < 0.15
