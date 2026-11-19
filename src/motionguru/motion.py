"""Deterministic 2D motion-graphics renderer: JSON scenes -> H.264 MP4.

Pillow draws frames and FFmpeg encodes them. No browser, cloud API or paid assets.
"""

from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from .media import require_tools

EASINGS = {
    "linear": lambda t: t,
    "ease-out": lambda t: 1 - (1 - t) ** 3,
    "ease-in": lambda t: t ** 3,
    "ease-in-out": lambda t: t * t * (3 - 2 * t),
}


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def validate_project(project: dict[str, Any]) -> None:
    if not isinstance(project, dict):
        raise ValueError("Motion project must be a JSON object")
    width, height, fps = (project.get("width", 1080), project.get("height", 1920),
                          project.get("fps", 30))
    if not all(isinstance(x, int) for x in (width, height, fps)):
        raise ValueError("Width, height and fps must be integers")
    if width < 32 or height < 32 or width > 3840 or height > 3840:
        raise ValueError("Dimensions must be between 32 and 3840 pixels")
    if width % 2 or height % 2 or not 1 <= fps <= 60:
        raise ValueError("Dimensions must be even; fps must be between 1 and 60")
    scenes = project.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise ValueError("At least one scene is required")
    total = 0.0
    for scene in scenes:
        if not isinstance(scene, dict):
            raise ValueError("Each scene must be an object")
        d = scene.get("duration")
        if not isinstance(d, (int, float)) or not math.isfinite(d) or not 0 < d <= 300:
            raise ValueError("Each scene duration must be positive and <= 300 seconds")
        total += d
        layers = scene.get("layers", [])
        if not isinstance(layers, list) or len(layers) > 100:
            raise ValueError("Each scene supports up to 100 layers")
        for layer in layers:
            if not isinstance(layer, dict) or layer.get("type") not in ("text", "rect", "circle", "line", "chart", "counter"):
                raise ValueError("Unsupported layer. Use text, rect, circle, line, chart or counter")
    if total > 1800:
        raise ValueError("Total project duration must be at most 30 minutes")


def load_project(path: Path) -> dict:
    project = json.loads(path.read_text(encoding="utf-8"))
    validate_project(project)
    return project


def font_for(size: int, preferred: str | None = None):
    candidates = [preferred] if preferred else []
    candidates += [
        "DejaVuSans-Bold.ttf",
        "Arial.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for candidate in candidates:
        if candidate:
            try:
                return ImageFont.truetype(candidate, max(8, size))
            except OSError:
                pass
    return ImageFont.load_default()


def position(layer: dict, width: int, height: int) -> tuple[int, int]:
    return int(float(layer.get("x", 0.5)) * width), int(float(layer.get("y", 0.5)) * height)


def draw_frame(project: dict, seconds: float) -> Image.Image:
    """Render a frame at an absolute project timestamp."""
    validate_project(project)
    width, height = project.get("width", 1080), project.get("height", 1920)
    cursor = 0.0
    selected = project["scenes"][-1]
    local = float(selected["duration"])
    for scene in project["scenes"]:
        d = float(scene["duration"])
        if seconds < cursor + d:
            selected, local = scene, seconds - cursor
            break
        cursor += d

    canvas = Image.new("RGB", (width, height), selected.get("background", "#101827"))
    draw = ImageDraw.Draw(canvas)
    scene_duration = float(selected["duration"])
    fade = float(selected.get("scene_fade", 0.2))
    for layer in selected.get("layers", []):
        start = float(layer.get("start", 0))
        end = float(layer.get("end", scene_duration))
        if not start <= local <= end or end <= start:
            continue
        x, y = position(layer, width, height)
        speed = max(0.01, float(layer.get("entrance_duration", 0.4)))
        progress = EASINGS["ease-out"](clamp((local - start) / speed))
        exit_p = EASINGS["ease-in"](clamp((end - local) / max(0.01, float(layer.get("exit_duration", 0.2)))))
        visible = min(progress, exit_p)
        entrance = layer.get("entrance", "fade-up")
        if entrance == "fade-up":
            y += int((1-progress) * 0.055 * height)
        elif entrance == "slide-left":
            x += int((1-progress) * 0.15 * width)
        elif entrance == "slide-right":
            x -= int((1-progress) * 0.15 * width)
        elif entrance == "zoom":
            pass
        color = layer.get("color", "#FFFFFF")
        kind = layer["type"]
        if kind in ("text", "counter"):
            content = str(layer.get("text", ""))
            if kind == "counter":
                begin, finish = float(layer.get("from", 0)), float(layer.get("to", 100))
                value = begin + (finish - begin) * EASINGS["ease-out"](clamp((local-start)/(end-start)))
                content = f"{value:,.{int(layer.get('decimals', 0))}f}{layer.get('suffix','')}"
            if entrance == "typewriter":
                content = content[:math.ceil(len(content) * progress)]
            size = int(float(layer.get("size", 80)) * (0.75 + 0.25 * progress) if entrance == "zoom" else layer.get("size", 80))
            font = font_for(size, layer.get("font"))
            anchor = layer.get("anchor", "mm")
            # Draw on an alpha layer, so fade transitions work on every color.
            foreground = Image.new("RGBA", canvas.size)
            fg = ImageDraw.Draw(foreground)
            fg.text((x, y), content, fill=color, font=font, anchor=anchor,
                    stroke_width=int(layer.get("stroke_width", 0)),
                    stroke_fill=layer.get("stroke_color", "#000000"))
            foreground.putalpha(foreground.getchannel("A").point(lambda a: int(a*visible)))
            canvas.paste(foreground, (0, 0), foreground)
            draw = ImageDraw.Draw(canvas)
        elif kind == "rect":
            rw, rh = float(layer.get("width", 0.3)), float(layer.get("height", 0.1))
            draw.rounded_rectangle((x, y, x+int(rw*width*progress), y+int(rh*height)),
                                   radius=int(layer.get("radius", 12)), fill=color)
        elif kind == "circle":
            r = float(layer.get("radius", 0.08)) * min(width, height) * progress
            draw.ellipse((x-r, y-r, x+r, y+r), fill=color)
        elif kind == "line":
            end_x = int(float(layer.get("x2", 0.9))*width)
            end_y = int(float(layer.get("y2", 0.5))*height)
            draw.line((x,y,x+(end_x-x)*progress,y+(end_y-y)*progress), fill=color,
                      width=int(layer.get("thickness", 6)))
        elif kind == "chart":
            values = layer.get("values", [12, 20, 15, 35, 40])
            if not isinstance(values, list) or len(values) < 2 or len(values) > 200:
                raise ValueError("Chart must contain 2–200 numbers")
            values = [float(v) for v in values]
            if not all(math.isfinite(v) for v in values):
                raise ValueError("Chart numbers must be finite")
            chart_w = float(layer.get("width", 0.75))*width
            chart_h = float(layer.get("height", 0.25))*height
            minimum, maximum = min(values), max(values)
            span = max(1e-9, maximum-minimum)
            points = [(x + chart_w*i/(len(values)-1),
                       y + chart_h * (1-(v-minimum)/span)) for i,v in enumerate(values)]
            n = max(2, min(len(points), 1+math.ceil((len(points)-1)*progress)))
            draw.line(points[:n], fill=color, width=int(layer.get("thickness", 6)),
                      joint="curve")
    if fade > 0:
        opacity = min(1.0, max(0.0, local/fade), max(0.0, (scene_duration-local)/fade))
        if opacity < 1:
            background = Image.new("RGB", (width,height), project.get("background", "#080D16"))
            canvas = Image.blend(background, canvas, opacity)
    return canvas


def render_motion(project: dict, output: Path, *, preview: Path | None = None) -> dict:
    validate_project(project)
    width, height, fps = project.get("width",1080), project.get("height",1920), project.get("fps",30)
    duration = sum(float(s["duration"]) for s in project["scenes"])
    frames = math.ceil(duration*fps)
    if preview is not None:
        preview.parent.mkdir(parents=True,exist_ok=True)
        draw_frame(project, duration*0.5).save(preview)
        return {"preview": str(preview), "frames": 1, "duration": duration}
    require_tools()
    output.parent.mkdir(parents=True,exist_ok=True)
    cmd = ["ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
           "-f","rawvideo","-vcodec","rawvideo","-s",f"{width}x{height}",
           "-pix_fmt","rgb24","-r",str(fps),"-i","-",
           "-an","-c:v","libx264","-pix_fmt","yuv420p",
           "-movflags","+faststart",str(output)]
    proc = subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        assert proc.stdin is not None
        for i in range(frames):
            proc.stdin.write(draw_frame(project, i/fps).tobytes())
        proc.stdin.close()
        rc = proc.wait()
        if rc:
            raise RuntimeError(f"FFmpeg rendering failed with code {rc}")
    except (BrokenPipeError,OSError):
        proc.kill()
        proc.wait()
        raise RuntimeError("FFmpeg failed while receiving animation frames")
    return {"output":str(output),"duration":duration,"frames":frames}
