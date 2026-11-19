# MotionGuru AI by Chaituverse

**Create. Animate. Edit. With AI.**

A local-first, open-source video editing and motion-graphics project. The first working milestone focuses on **reviewable, non-destructive silence cuts**. Motion graphics, premium captions, smart semantic cuts, SFX packs, and a visual studio are planned rather than claimed as shipped.

## Phase 1 — smart cuts

Requirements: Python 3.10+ and FFmpeg (both `ffmpeg` and `ffprobe` on PATH). Works on Windows, macOS, and Linux.

### Windows quick start

```powershell
git clone https://github.com/Chaitukarpurapu/MotionGuru-AI-by-Chaituverse.git
cd MotionGuru-AI-by-Chaituverse
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
ffmpeg -version
```

### Analyze, review, render

```powershell
motionguru analyze "input.mp4" --output "cuts.json"
motionguru review "cuts.json"
motionguru render "input.mp4" --decisions "cuts.json" --output "edited.mp4"
```

- `analyze` detects silence using FFmpeg `silencedetect` and writes suggested cut ranges with **pending** decisions.
- `review` interactively asks for `cut` or `keep` for each range and records decisions.
- `render` **refuses to run** if any proposal remains pending; renders approved cuts by concatenating the remaining timeline portions. Original source is not overwritten.
- Analyzed silences are **proposals**, not proof that content is unwanted. The creator decides.
- The prototype re-encodes H.264 and AAC. It is intended for short videos; very long projects and sophisticated audio mixing are future work.

### Run tests

```powershell
python -m pytest
```

## Roadmap

| Version | Goal | Status |
| --- | --- | --- |
| 0.1 | FFmpeg metadata, silence proposals, manual approval, MP4 output | Initial implementation on feature branch |
| 0.2 | Caption transcription, timing correction, styled subtitles | Planned |
| 0.3 | Kinetic typography and motion-graphics scene renderer | Planned |
| 0.4 | SFX, voice/music mixing, advanced video effects | Planned |
| 0.5 | AI assistant tool interface and preview studio | Planned |

See [ARCHITECTURE.md](docs/ARCHITECTURE.md), [ROADMAP.md](ROADMAP.md), and [the Claude Code skill](.claude/skills/motionguru/SKILL.md).

## Attribution and licenses

This initial implementation is written independently. The uploaded `claude-reel-effects` project is an architectural reference; **its Python code, models, fonts, logos, and sound effects are not bundled here**. Any future import must be audited for applicable licenses, preserving copyright notices, and asset usage rights. The new source in this repository is MIT-licensed; see [LICENSE](LICENSE).

Created by **Chaituverse**.
