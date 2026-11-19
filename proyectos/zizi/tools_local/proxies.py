#!/usr/bin/env python3
"""Proxies livianos (426x240, sin audio) + poster de cada toma, para el artefacto de selección."""
import json, subprocess, sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
A = Path(__file__).parent.parent; R = A.parent.parent
inv = json.load(open(A / "inventario/inventario.json"))
def one(c):
    n = c["n"]
    if n >= 150: return
    src = R / c["file"]; out = A / f"artefacto/media/t{n:03d}.mp4"; pos = A / f"artefacto/posters/t{n:03d}.jpg"
    if not out.exists():
        subprocess.run(["ffmpeg","-v","error","-y","-skip_loop_filter","all","-skip_frame","noref","-i",str(src),"-an","-vf","scale=426:240:force_original_aspect_ratio=increase,crop=426:240",
            "-c:v","libx264","-preset","veryfast","-crf","31","-g","15","-pix_fmt","yuv420p","-movflags","+faststart",str(out)],check=True)
    if not pos.exists():
        subprocess.run(["ffmpeg","-v","error","-y","-ss",f"{c['duracion']*0.35:.2f}","-i",str(out),"-frames:v","1","-q:v","6",str(pos)],check=True)
with ThreadPoolExecutor(4) as ex: list(ex.map(one, inv))
print("ok")
