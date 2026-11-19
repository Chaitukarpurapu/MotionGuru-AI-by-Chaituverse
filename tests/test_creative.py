"""Motion graphics, captions and original sound design smoke tests."""

import json
import shutil
import wave
from pathlib import Path

import pytest

from motionguru.audio import generate_sfx
from motionguru.captions import ass_from_segments, parse_srt, srt_from_segments
from motionguru.cli import main
from motionguru.motion import draw_frame, load_project, validate_project
from motionguru.media import probe


def sample_project():
    return {
        "width": 160, "height": 288, "fps": 12,
        "scenes": [
            {"duration": 1, "background": "#101820",
             "layers": [
                 {"type": "text", "text": "MOTIONGURU", "x": 0.5, "y": 0.4,
                  "size": 19, "color": "#FFFFFF", "entrance": "fade-up"},
                 {"type": "chart", "x": .1, "y": .6, "width": .8,
                  "height": .2, "values": [1,3,2,5,9], "color": "#5CE1E6"}
             ]}
        ]
    }


def test_motion_frame_is_expected_size():
    frame = draw_frame(sample_project(), 0.5)
    assert frame.size == (160,288)
    assert frame.mode == "RGB"


def test_motion_validator_rejects_unknown_layer():
    p = sample_project()
    p["scenes"][0]["layers"][0]["type"] = "untrusted_effect"
    with pytest.raises(ValueError, match="Unsupported layer"):
        validate_project(p)


def test_srt_to_ass_styles_and_timestamps():
    segments = parse_srt(
        "1\n00:00:00,000 --> 00:00:00,950\nHello world\n\n"
        "2\n00:00:01,000 --> 00:00:02,250\nWelcome back\n"
    )
    assert len(segments)==2
    output = ass_from_segments(segments,style="editorial",width=720,height=1280)
    assert "Dialogue:" in output
    assert "Hello world" in output
    assert "PlayResX: 720" in output
    assert "00:00:00,950" in srt_from_segments(segments)


@pytest.mark.parametrize("kind",["impact","whoosh","riser","pop","click","sweep"])
def test_original_sfx_wav(tmp_path,kind):
    target=tmp_path/f"{kind}.wav"
    generate_sfx(kind,target,duration=.08)
    with wave.open(str(target),"rb") as stream:
        assert stream.getnchannels()==1
        assert stream.getnframes()>2000


@pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
                    reason="FFmpeg and ffprobe required")
def test_motion_render_real_mp4(tmp_path):
    project=sample_project()
    source=tmp_path/"scene.json"
    output=tmp_path/"scene.mp4"
    source.write_text(json.dumps(project),encoding="utf-8")
    assert main(["motion",str(source),"--output",str(output)])==0
    info=probe(output)
    assert 0.85 < info["duration"] < 1.15
    assert output.stat().st_size>400


def test_preview_png(tmp_path):
    source=tmp_path/"scene.json"
    output=tmp_path/"scene.png"
    source.write_text(json.dumps(sample_project()),encoding="utf-8")
    assert main(["motion",str(source),"--output","unused.mp4",
                 "--preview",str(output)])==0
    assert output.is_file()
