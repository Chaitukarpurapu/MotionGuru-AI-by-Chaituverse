# MotionGuru AI technical architecture

## Current packages

```
Claude Code skill / local MCP server / local CLI
                      |
          CLI + validation layer
           /         |         \
     Smart cuts    Motion      Captions
       FFmpeg    Pillow+FFmpeg SRT/ASS/Whisper
           \         |         /
             Basic Audio / SFX
                      |
              MP4 + JSON + WAV
```

### `src/motionguru/core.py`
Pure cut-interval validation and kept-range computation. Rendering will reject any pending decision. Source files must never be overwritten.

### `src/motionguru/media.py`
Runs ffprobe and FFmpeg through argument arrays, not a shell. Silence proposal generation and approved trim/concat export.

### `src/motionguru/motion.py`
Validates scene descriptions and draws deterministic RGB frames using Pillow. FFmpeg encodes the video. JSON scene elements: text, counter, rectangle, circle, line and chart. Coordinates are relative (0.0 to 1.0), sizes are pixel-based for fonts, and start/end are scene-relative seconds. This is a CPU renderer.

### `src/motionguru/captions.py`
Parses SRT and generates simple ASS style variants. Optional faster-whisper creates timestamped captions; the human must review transcription and timing. A temporary filename avoids Windows `ass` filter path escaping during burning.

### `src/motionguru/audio.py`
Synthesizes royalty-free original sound effects as mono WAV files and mixes audio inputs into an MP4 using FFmpeg filters.

### `src/motionguru/mcp_server.py`
Opt-in assistant tool interface. It exposes video inspection, silence cut proposals, reviewed-cut rendering and scene-file rendering through local stdio. These are filesystem-capable tools: do not run the server for untrusted remote agents.

### `src/motionguru/studio`
Single-page local scene JSON editor and browser canvas preview. Export JSON, render final MP4 with the CLI. This is not a full multitrack NLE.

## Security and quality

- No shell string interpolation of filenames.
- Strict validation for project duration, dimensions, supported layer types and edit decisions.
- Explicit review required for detected cuts.
- No third-party proprietary media bundled.
- Planned next: isolated project workspace, per-operation file authorizations, signed effect-pack manifests, speech-aware editing, GPU compositing, design QA.

## Future architecture

Add a typed multitrack timeline, reusable effects registry, deterministic keyframe engine, caption effect plugin system, headless preview server, and a scheduling layer for sound and visual synchronization.

Avoid importing other repositories' code or commercial assets without license audits. Remotion integrations require an independent license check for video-editor use cases.
