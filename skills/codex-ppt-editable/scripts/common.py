"""Shared data helpers for the editable extension. MIT; Copyright 2026 1nnnnnn9."""
from __future__ import annotations
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))

def write_json(path, data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with NamedTemporaryFile("w",encoding="utf-8",dir=path.parent,delete=False) as f:
        json.dump(data,f,ensure_ascii=False,indent=2);f.write("\n");temp=f.name
    os.replace(temp,path)

def resolve(root, value):
    p=Path(value).expanduser()
    return p.resolve() if p.is_absolute() else (Path(root)/p).resolve()

def load_spec(path):
    path=Path(path).expanduser().resolve();d=read_json(path)
    if not isinstance(d,dict) or not isinstance(d.get("slides"),list) or not d["slides"]:
        raise ValueError("Spec needs a non-empty slides array")
    numbers=[s.get("number") for s in d["slides"]]
    if any(type(n) is not int or n<1 for n in numbers) or len(set(numbers))!=len(numbers):
        raise ValueError("Slide numbers must be unique positive integers")
    canvas=d.get("canvas",{"width":1280,"height":720})
    if any(not isinstance(canvas.get(k), (int,float)) or canvas[k]<=0 for k in ("width","height")):
        raise ValueError("Canvas width/height must be positive")
    return path,d

def check_box(box,canvas,label):
    if not isinstance(box,list) or len(box)!=4 or any(not isinstance(n,(int,float)) for n in box):
        raise ValueError(f"{label}: box must be [x,y,width,height]")
    x,y,w,h=box
    if min(x,y)<0 or min(w,h)<=0 or x+w>canvas["width"]+0.01 or y+h>canvas["height"]+0.01:
        raise ValueError(f"{label}: object lies outside canvas")
    return box

def asset_map(spec):
    assets=spec.get("assets",[]);ids=[a["id"] for a in assets]
    if len(set(ids))!=len(ids):raise ValueError("Duplicate asset ids")
    return dict(zip(ids,assets))

def source_for_image(image,assets):
    if image.get("asset_id"):
        if image["asset_id"] not in assets:raise ValueError("Unknown asset_id: "+image["asset_id"])
        return assets[image["asset_id"]]["path"]
    if not image.get("path"):raise ValueError("Image needs asset_id or path")
    return image["path"]

def check_assets(spec):
    assets=asset_map(spec)
    used={im["asset_id"] for s in spec["slides"] for im in s.get("images",[]) if im.get("asset_id")}
    used|={t["asset_id"] for s in spec["slides"] for t in s.get("tables",[]) if t.get("asset_id")}
    unknown=used-set(assets)
    if unknown:raise ValueError("Unknown asset ids: "+", ".join(sorted(unknown)))
    for aid,a in assets.items():
        if aid not in used:
            if a.get("required"):raise ValueError("Required asset unused: "+aid)
            if not str(a.get("unused_reason","")).strip():raise ValueError("Unused asset needs unused_reason: "+aid)
    return assets
