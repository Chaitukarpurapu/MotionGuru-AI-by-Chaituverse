# Architecture

## v0.1 (implemented foundation)

- `src/motionguru/cli.py`: entry point, approval workflow, project JSON.
- `src/motionguru/core.py`: pure interval validation and non-destructive edit decision logic.
- `src/motionguru/media.py`: ffprobe inspection, FFmpeg silencedetect, trim/concat rendering.
- `.claude/skills/motionguru/SKILL.md`: Claude Code operating instructions.

Source media is left untouched. Edit decisions are stored outside the media file. The renderer rejects pending proposals.

## Planned expansion

- Structured editable multi-track timeline with typed scene and effect components.
- Motion renderer (TypeScript, SVG/Canvas, browser capture + FFmpeg).
- Captions and multilingual alignment.
- SFX synthesis and licensed asset packs, audio ducking and LUFS normalization.
- Human-in-the-loop semantic cut proposals with frame/audio previews.
- Assistant-neutral CLI, local MCP server and optional graphical studio.
- Plugin system with effects manifest, version checks and license metadata.

Remotion integration may be explored separately after reviewing its editor-related license provisions.

## Design rules

1. Never destructively modify the source.
2. Never apply cuts without an explicit decision.
3. Preserve timestamps and provenance for every edit.
4. Separate AI planning from deterministic rendering.
5. Validate video output and make all actions reproducible.
6. Do not redistribute models, fonts, SFX, logos or template assets without proper rights.
