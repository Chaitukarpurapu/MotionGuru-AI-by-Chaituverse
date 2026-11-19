"""Optional assistant-neutral local MCP tools; install pip extra [agents]."""

from __future__ import annotations

from pathlib import Path

from .core import make_silence_proposals, kept_intervals
from .media import probe, detect_silences, render_intervals
from .motion import load_project, render_motion


def main():
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError("Install MCP extras: pip install -e '.[agents]'") from exc

    server=FastMCP("MotionGuru AI")

    @server.tool()
    def inspect_video(source: str) -> dict:
        """Inspect a local video. Read-only."""
        return probe(Path(source).resolve())

    @server.tool()
    def propose_silence_cuts(source: str, noise_db: int=-35, min_silence: float=0.65) -> dict:
        """Propose, but DO NOT apply, removal of quiet sections."""
        path=Path(source).resolve()
        metadata=probe(path)
        intervals=(detect_silences(path,metadata["duration"],noise_db=noise_db,
                                  min_duration=min_silence) if metadata["has_audio"] else [])
        return {"source":str(path),"duration":metadata["duration"],
                "proposals":make_silence_proposals(intervals,metadata["duration"])}

    @server.tool()
    def export_reviewed_cuts(source: str, output: str, proposals: list[dict]) -> str:
        """Export cuts ONLY when every proposal explicitly says cut or keep."""
        src=Path(source).resolve()
        dst=Path(output).resolve()
        metadata=probe(src)
        project={"duration":metadata["duration"],"proposals":proposals}
        intervals=kept_intervals(project)
        render_intervals(src,dst,intervals,metadata["has_audio"])
        return str(dst)

    @server.tool()
    def render_scene_file(project_file: str, output: str) -> dict:
        """Render an existing JSON motion-scene project into MP4."""
        return render_motion(load_project(Path(project_file)),Path(output).resolve())

    server.run(transport="stdio")


if __name__=="__main__":
    main()
