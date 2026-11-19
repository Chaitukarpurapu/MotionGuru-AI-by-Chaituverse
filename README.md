# MotionGuru AI by Chaituverse

**Create. Animate. Edit. With AI.**

[![Tests](https://github.com/Chaitukarpurapu/MotionGuru-AI-by-Chaituverse/actions/workflows/tests.yml/badge.svg)](https://github.com/Chaitukarpurapu/MotionGuru-AI-by-Chaituverse/actions)

A **local-first, open-source** video editing and motion-graphics toolkit with an assistant-neutral CLI, a Claude Code skill, and an optional local MCP server. Built by **Chaituverse**.

> **Status:** Early developer preview. The repo includes a working foundation for manual-approved silence cuts, basic 2D motion scenes, SRT/ASS captions, offline speech transcription (optional), synthesized SFX, audio mixing and a basic browser scene preview. This is **not yet** a professional After Effects/Premiere/FluxoCut replacement.

## What works today

| Feature | Current capability |
| --- | --- |
| Smart cuts | FFmpeg silence detection; explicit cut/keep review; non-destructive MP4 export |
| Motion graphics | Render JSON scenes with animated text, shapes, lines, charts and counters |
| Captions | Convert SRT to 8 original ASS styles; optional word-level offline transcription; burn styles into MP4 |
| SFX | Create 6 original synthesized effects: impact, whoosh, riser, pop, click, sweep |
| Audio | Mix voice, music and SFX into MP4; adjustable volumes |
| AI integration | Claude Code skill + optional local MCP server; no cloud key required for deterministic tools |
| Scene Studio | Local browser preview and JSON editor at localhost, export editable JSON |
| Tests | Windows and Ubuntu tests; actual FFmpeg video-editing and motion-graphics smoke tests |

## Requirements

- **Python 3.10+**, tested in CI on Python 3.12.
- **FFmpeg and ffprobe** on your PATH for rendering/editing.
- **Pillow** (installed automatically).
- Optional `faster-whisper` and a local model download for transcription.
- Optional `mcp` package for agent tools.

### Install on Windows PowerShell

```powershell
git clone https://github.com/Chaitukarpurapu/MotionGuru-AI-by-Chaituverse.git
cd MotionGuru-AI-by-Chaituverse
git checkout feat/phase1-smart-cuts
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
ffmpeg -version
motionguru --help
```

### 1. AI-assisted, human-approved cuts

```powershell
motionguru analyze "input.mp4" --output "cuts.json"
motionguru review "cuts.json"
motionguru render "input.mp4" --decisions "cuts.json" --output "edited.mp4"
```

All proposals default to `pending`. Render **refuses to export** while an unreviewed proposal exists. Silence is not necessarily unwanted content.

### 2. Create motion graphics from scratch

```powershell
motionguru motion "examples/intro.json" --output "intro.mp4"
motionguru motion "examples/intro.json" --output "unused.mp4" --preview "preview.png"
```

Use the editable JSON scene schema to control text, shapes, charts, colors, time, easing and composition. Default example is a 7.5-second 720×1280 vertical reel.

### 3. Professional-style captions

```powershell
motionguru captions style "examples/captions.srt" --style editorial --output "captions.ass"
motionguru captions burn "input.mp4" --captions "captions.ass" --output "captioned.mp4"
```

Styles: `clean`, `editorial`, `pop`, `cinematic`, `neon`, `minimal`, `bold`, `lower-third`. These are original, simple ASS typography presets—not proprietary commercial Envato templates. Burning requires an FFmpeg build with the ASS/libass filter.

For optional offline speech-to-text:

```powershell
python -m pip install -e ".[transcribe]"
motionguru captions transcribe "voiceover.mp3" --language te --output "words.srt"
```

On the first transcription, faster-whisper may download a model. Word timestamps are approximate and must be checked by a human, especially for Telugu-English code switching.

### 4. Create original sound effects and mix audio

```powershell
motionguru sfx whoosh --duration 0.7 --output "whoosh.wav"
motionguru mix "intro.mp4" --sfx "whoosh.wav" --output "intro-sound.mp4"
motionguru mix "video.mp4" --music "licensed-music.mp3" --music-volume 0.15 --output "mix.mp4"
```

Only use music that you have a license to use. Audio mixing is basic volume balancing; advanced beat sync, ducking and mastering are planned.

### 5. Local scene studio

```powershell
motionguru studio
```

Open **http://127.0.0.1:8765** to preview or edit JSON scenes. The web editor is local and does not upload media. Export scene JSON and render final MP4 with the CLI. Its preview is not guaranteed to be pixel-identical to the Python renderer.

### 6. Claude Code & other agents

The skill is in `.claude/skills/motionguru/SKILL.md`. It explains how to plan scene JSON, review cuts and render/export safely.

Optional MCP tools:

```powershell
python -m pip install -e ".[agents]"
motionguru-mcp
```

Configure your compatible assistant to launch `motionguru-mcp` as a local stdio server. Do not expose it to untrusted remote users; it accesses local files on behalf of the user.

## Run tests

```powershell
python -m pytest -q
```

See [Quick Start](docs/QUICKSTART.md), [Architecture](docs/ARCHITECTURE.md), [Roadmap](ROADMAP.md) and [Testing](docs/TESTING.md).

## Licensing and original effects

The MotionGuru code is MIT licensed. No third-party commercial templates, premium SFX, model weights, logo packs or fonts have been copied into the repository. The original Claude Reel Effects repository informed our architecture; future code reuse must carry correct third-party notices and asset licenses.

Copyright (c) 2026 Chaituverse.
