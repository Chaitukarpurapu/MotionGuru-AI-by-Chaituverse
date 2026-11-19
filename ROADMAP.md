# MotionGuru AI roadmap

## Implemented in developer preview (verify with GitHub Actions before merging)

- [x] Python CLI and Windows/Linux installation
- [x] Video metadata and FFmpeg silence analysis
- [x] User-approved non-destructive cuts
- [x] JSON motion scenes: text, shape, chart, counter and timing
- [x] Pillow-to-FFmpeg H.264 frame renderer
- [x] SRT parsing, ASS output and eight original styles
- [x] Optional offline word timestamps via faster-whisper
- [x] Six original synthesized SFX
- [x] Basic FFmpeg audio mixing
- [x] Claude Code skill and optional local MCP server
- [x] Browser scene JSON preview/edit
- [x] CI and unit/smoke tests

## Next improvements

- [ ] Stabilize Windows and Ubuntu CI for the new modules
- [ ] Full transcript-aware cut proposals with user review clips
- [ ] Fully synced per-word animated captions with punctuation correction
- [ ] Auto-layout typography: wrapping, vertical safe areas, collision checks
- [ ] Per-layer keyframe tracks, editable interpolation curves and animated masks
- [ ] Motion-tracked footage compositing, object segmentation, chroma key
- [ ] Audio ducking, EQ, limiter, beat detection and SFX timeline placement
- [ ] Modern GPU-accelerated rendering and frame caching
- [ ] Visual multitrack non-linear timeline with undo history and waveform previews
- [ ] Plugin SDK, installable style packs, validation and community asset licenses
- [ ] Agent sandboxing and user-file permission controls
- [ ] Benchmark renders and real-device performance tests

**No unimplemented feature is advertised as shipped.**
