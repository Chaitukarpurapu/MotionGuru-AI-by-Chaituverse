"""Original procedurally generated SFX and basic FFmpeg audio mixing."""

from __future__ import annotations

import math
import random
import struct
import subprocess
import wave
from pathlib import Path

from .media import probe, require_tools

SFX_KINDS=("impact","whoosh","riser","pop","click","sweep")


def generate_sfx(kind: str, output: Path, *, duration: float=0.65, sample_rate:int=44100):
    if kind not in SFX_KINDS:
        raise ValueError(f"Unknown SFX kind: {kind}")
    if not 0.05<=duration<=10:
        raise ValueError("SFX duration must be between 0.05 and 10 seconds")
    rng=random.Random(12)
    count=int(duration*sample_rate)
    output.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(output),"wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        frames=bytearray()
        phase=0.0
        for i in range(count):
            t=i/sample_rate
            p=t/duration
            if kind=="impact":
                freq=105*(1-p)**2+36
                env=math.exp(-8*p)
                value=math.sin(2*math.pi*freq*t)*0.72+ (rng.random()*2-1)*0.28
            elif kind=="whoosh":
                env=math.sin(math.pi*p)**1.5
                freq=250+1600*p
                value=0.6*(rng.random()*2-1)+0.4*math.sin(2*math.pi*freq*t)
            elif kind=="riser":
                env=p**1.5 * max(0.0,(1-p)*10)
                freq=120+1300*p*p
                phase+=2*math.pi*freq/sample_rate
                value=0.8*math.sin(phase)+0.2*(rng.random()*2-1)
            elif kind=="pop":
                env=math.exp(-18*p)
                value=math.sin(2*math.pi*(600-400*p)*t)
            elif kind=="click":
                env=math.exp(-35*p)
                value=rng.random()*2-1
            else:
                env=math.sin(math.pi*p)
                freq=500+1600*math.sin(math.pi*p)
                value=0.7*(rng.random()*2-1)+0.3*math.sin(2*math.pi*freq*t)
            amplitude=max(-1.0,min(1.0,value*env*0.7))
            frames.extend(struct.pack("<h",int(amplitude*32767)))
        f.writeframes(frames)
    return output


def mix_audio(video:Path, output:Path, *, music:Path|None=None,
              sfx:Path|None=None, music_volume:float=0.2, sfx_volume:float=0.6):
    require_tools()
    if video.resolve()==output.resolve():
        raise ValueError("Output must be a new file")
    if music is None and sfx is None:
        raise ValueError("Provide --music or --sfx")
    if not 0<=music_volume<=2 or not 0<=sfx_volume<=2:
        raise ValueError("Volumes must be between 0 and 2")
    meta=probe(video)
    cmd=["ffmpeg","-hide_banner","-nostdin","-y","-i",str(video.resolve())]
    sources=[]
    tracks=[]
    if meta["has_audio"]:
        tracks.append("[0:a:0]aresample=async=1:first_pts=0[voice]")
        sources.append("[voice]")
    index=1
    for name,file,level in (("music",music,music_volume),("sfx",sfx,sfx_volume)):
        if file is not None:
            if not file.is_file():
                raise FileNotFoundError(file)
            cmd+=["-stream_loop","-1","-i",str(file.resolve())] if name=="music" else ["-i",str(file.resolve())]
            tracks.append(f"[{index}:a:0]volume={level},aresample=async=1:first_pts=0[{name}]")
            sources.append(f"[{name}]")
            index+=1
    tracks.append("".join(sources)+f"amix=inputs={len(sources)}:duration=longest:dropout_transition=0,alimiter=limit=0.95[mixed]")
    cmd+=["-filter_complex",";".join(tracks),"-map","0:v:0","-map","[mixed]",
          "-c:v","copy","-c:a","aac","-b:a","192k","-t",str(meta["duration"]),
          "-movflags","+faststart",str(output.resolve())]
    output.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(cmd,check=True)
