# Testing MotionGuru AI (Phase 1)

## Continuous integration

The GitHub Actions workflow runs on **Windows and Ubuntu** using Python 3.12. It installs FFmpeg and tests both time-interval logic and real MP4 editing.

## Locally (Windows PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
ffmpeg -version
ffprobe -version
python -m pytest -q
```

## Key checks

- Three seconds of generated color video and audio with a silent middle second can be analyzed.
- Proposed edits default to `pending`.
- Rendering is blocked until every proposed edit has an explicit decision.
- An approved removal reduces the output's duration.
- A rejected removal preserves duration.
- The original video stays unchanged.
- Output has a playable video stream and audio stream.

## Notes

The synthetic test uses tones, not speech. It does not validate speech recognition, semantic editing, voice synchronization, or high-end graphics. Frame-accurate variable-frame-rate footage and multi-track media remain outside this prototype.
