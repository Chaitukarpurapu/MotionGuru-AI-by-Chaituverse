# Quick Start and editing recipes

## Windows setup

1. Install Python 3.10+ and FFmpeg; make sure `ffmpeg` and `ffprobe` can run from PowerShell.
2. Clone the repository and check out `feat/phase1-smart-cuts` while the pull request remains open.
3. Run `py -m venv .venv`, `.\.venv\Scripts\Activate.ps1`, and `pip install -e ".[dev]"`.
4. Try `motionguru motion examples/intro.json --output intro.mp4`.

## Use the browser editor

`motionguru studio` starts a localhost-only server. Open http://127.0.0.1:8765. Load `examples/intro.json`, change text, adjust animation timing, preview it and export the edited JSON.

## Generate SFX

`motionguru sfx impact --duration .5 --output impact.wav`

For a silent motion video, add the SFX with `motionguru mix intro.mp4 --sfx impact.wav --output result.mp4`. A short SFX will only play once.

## Add subtitles

`motionguru captions style examples/captions.srt --style bold --output captions.ass`

`motionguru captions burn intro.mp4 --captions captions.ass --output captioned.mp4`

Only original caption styling is bundled. A future engine will support real kinetic word transitions, per-word highlight animations, masking and brand templates.

## Assistant workflow

Ask the assistant to generate JSON following `examples/intro.json`. Save it locally, validate by rendering a preview PNG, then render the MP4. All voiceover scripts and transcript-derived edits should be checked before publication.

## Current limits

- No GUI non-linear multitrack editor or native keyframe graph.
- No AI automatic edit generation from unrestricted natural-language prompts without an attached assistant.
- No trained semantic filler/retake detector; silence detection only.
- No professional color pipeline, GPU renderer or motion tracking in the new modules.
- Some fonts vary by operating system and commercial template assets are not redistributed.
- Motion rendering is CPU-bound; a 4K clip can be slow.
