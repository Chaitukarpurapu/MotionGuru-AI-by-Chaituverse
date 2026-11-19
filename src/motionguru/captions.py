"""SRT and stylized ASS captions; optional offline faster-whisper transcription."""

from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path
from shutil import copyfile

STYLES = {
    "clean": ("Arial", 56, "&H00FFFFFF", "&H00000000", 1),
    "editorial": ("Arial", 76, "&H00FFFFFF", "&H00000000", 1),
    "pop": ("Arial", 86, "&H0000DFFF", "&H00000000", 3),
    "cinematic": ("Arial", 64, "&H00E9D4A5", "&H00000000", 2),
    "neon": ("Arial", 72, "&H00FBCD65", "&H001B1121", 3),
    "minimal": ("Arial", 48, "&H00FFFFFF", "&H00000000", 1),
    "bold": ("Arial", 88, "&H00FFFFFF", "&H00101010", 3),
    "lower-third": ("Arial", 50, "&H00FFFFFF", "&H00101010", 3),
}


def stamp(seconds: float, ass: bool = False) -> str:
    seconds = max(0.0,float(seconds))
    h = int(seconds//3600)
    m = int(seconds//60)%60
    s = int(seconds)%60
    if ass:
        return f"{h}:{m:02d}:{s:02d}.{int(round((seconds%1)*100)):02d}"
    return f"{h:02d}:{m:02d}:{s:02d},{int(round((seconds%1)*1000)):03d}"


def parse_srt(text: str) -> list[dict]:
    entries = []
    pattern = re.compile(r"(\d\d):(\d\d):(\d\d)[,.](\d+)\s*-->\s*(\d\d):(\d\d):(\d\d)[,.](\d+)")
    for block in re.split(r"\r?\n\s*\r?\n",text.strip()):
        lines = [x for x in block.splitlines() if x.strip()]
        if not lines:
            continue
        idx = next((i for i,line in enumerate(lines) if pattern.search(line)),None)
        if idx is None:
            continue
        m = pattern.search(lines[idx])
        assert m
        def seconds(part):
            h, minute, sec, milli = part
            return int(h)*3600+int(minute)*60+int(sec)+int(milli.ljust(3,"0")[:3])/1000
        start,end=seconds(m.groups()[:4]),seconds(m.groups()[4:])
        if end <= start:
            raise ValueError("Subtitle end must be after start")
        entries.append({"start":start,"end":end,"text":" ".join(lines[idx+1:])})
    return entries


def srt_from_segments(segments: list[dict]) -> str:
    blocks=[]
    for i,entry in enumerate(segments,1):
        if float(entry["end"]) <= float(entry["start"]):
            continue
        value=str(entry["text"]).strip()
        blocks.append(f"{i}\n{stamp(entry['start'])} --> {stamp(entry['end'])}\n{value}")
    return "\n\n".join(blocks)+"\n"


def ass_from_segments(segments: list[dict], *, style: str="editorial",
                      width: int=1080,height: int=1920) -> str:
    if style not in STYLES:
        raise ValueError("Caption style not found: "+style)
    font, size, color, outline, border = STYLES[style]
    size = max(14, round(size*height/1920))
    margin = max(16,int(height*0.12))
    header=f"""[Script Info]
Title: MotionGuru AI Captions
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: MotionGuru,{font},{size},{color},&H0000FFFF,{outline},&H80000000,-1,0,0,0,100,100,0,0,1,{border},1,2,48,48,{margin},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines=[]
    for seg in segments:
        value=str(seg["text"]).replace("{","(").replace("}",")").replace("\n",r"\N")
        # ASS is not HTML; escape backslashes to avoid style override injection.
        value=value.replace("\\",r"\\")
        lines.append(
            f"Dialogue: 0,{stamp(seg['start'],True)},{stamp(seg['end'],True)},MotionGuru,,0,0,0,,{value}"
        )
    return header+"\n".join(lines)+"\n"


def transcribe(media_path: Path, *, model_name: str="small",
               language: str | None=None) -> list[dict]:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError("Install transcription extras: pip install -e '.[transcribe]'") from exc
    model=WhisperModel(model_name,device="cpu",compute_type="int8")
    segments,_=model.transcribe(str(media_path),language=language,word_timestamps=True,
                               vad_filter=True)
    words=[]
    for segment in segments:
        if segment.words:
            for word in segment.words:
                if word.end>word.start and word.word.strip():
                    words.append({"start":word.start,"end":word.end,"text":word.word.strip()})
        elif segment.end>segment.start:
            words.append({"start":segment.start,"end":segment.end,"text":segment.text.strip()})
    return words


def burn_ass(video: Path, captions: Path, output: Path):
    """Use a short temporary ASS filename to avoid Windows FFmpeg filter path parsing."""
    from .media import require_tools, probe
    require_tools()
    if video.resolve()==output.resolve():
        raise ValueError("Cannot overwrite the original video")
    if not captions.is_file():
        raise FileNotFoundError(captions)
    meta=probe(video)
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="motionguru-captions-") as folder:
        copyfile(captions,Path(folder)/"captions.ass")
        cmd=["ffmpeg","-hide_banner","-nostdin","-y","-i",str(video.resolve()),
             "-vf","ass=captions.ass","-c:v","libx264","-pix_fmt","yuv420p"]
        if meta["has_audio"]:
            cmd+=["-c:a","aac","-b:a","192k"]
        else:
            cmd+=["-an"]
        cmd+=["-movflags","+faststart",str(output.resolve())]
        subprocess.run(cmd,cwd=folder,check=True)
