#!/usr/bin/env python3
"""Prepare a preview contact sheet and verify human visual-review evidence. MIT."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw
from common import load_spec, read_json, write_json, resolve
from visual_planning import validate_plans

CHECKS=("style_fidelity","visual_matches_plan","relations_correct","text_legible","background_text_free","sources_intact","data_correct")

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def spec_digest(path):
    # Git/Windows may normalize JSON line endings without changing the spec.
    canonical=json.dumps(read_json(path),sort_keys=True,ensure_ascii=False,separators=(",",":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

def prepare_review(spec_path,pptx,previews,output):
    path,spec=load_spec(spec_path);validate_plans(spec)
    if len(previews)!=len(spec["slides"]):raise ValueError("One rendered preview per slide is required, in spec order")
    if len({Path(p).resolve() for p in previews})!=len(previews):raise ValueError("Each slide needs its own preview path")
    output=Path(output).resolve();output.parent.mkdir(parents=True,exist_ok=True)
    columns=min(4,len(previews));cell_w,cell_h=400,249
    sheet=Image.new("RGB",(columns*cell_w,((len(previews)+columns-1)//columns)*cell_h),"#E8EDF2")
    rows=[]
    for i,(slide,preview) in enumerate(zip(spec["slides"],previews)):
        preview=Path(preview).resolve()
        with Image.open(preview) as im:
            if min(im.size)<100:raise ValueError("Preview is too small")
            thumb=ImageOps.contain(im.convert("RGB"),(384,216))
        x=(i%columns)*cell_w+8;y=(i//columns)*cell_h+8
        sheet.paste(thumb,(x,y));ImageDraw.Draw(sheet).text((x,y+218),str(slide["number"]),fill="#173552")
        rows.append({"number":slide["number"],"preview":str(preview),"sha256":digest(preview),
                     "checks":dict.fromkeys(CHECKS),"observation":""})
    montage=output.with_suffix(".montage.png");sheet.save(montage)
    result={"spec_sha256":spec_digest(path),"pptx":str(Path(pptx).resolve()),"pptx_sha256":digest(pptx),
            "montage":str(montage),"montage_sha256":digest(montage),
            "whole_deck":{"visual_balance":None,"later_section_quality":None,"observation":""},"slides":rows,
            "scope":"Human observations required. This template does not inspect or approve visual content automatically."}
    write_json(output,result);return result

def check_review(spec_path,pptx,review_path):
    path,spec=load_spec(spec_path);validate_plans(spec)
    review_path=Path(review_path).resolve();root=review_path.parent;review=read_json(review_path);errors=[]
    if review.get("spec_sha256")!=spec_digest(path):errors.append("Review spec is stale")
    if review.get("pptx_sha256")!=digest(pptx) or resolve(root,review.get("pptx",""))!=Path(pptx).resolve():errors.append("Review PPTX is stale")
    for kind in ("montage",):
        file=resolve(root,review.get(kind,""))
        if not file.is_file() or review.get(kind+"_sha256")!=digest(file):errors.append("Review montage is missing/stale")
    whole=review.get("whole_deck",{})
    if any(whole.get(k) is not True for k in ("visual_balance","later_section_quality")) or not str(whole.get("observation","")).strip():
        errors.append("Whole-deck/later-section visual review is incomplete")
    entries=review.get("slides",[])
    if [s.get("number") for s in entries]!=[s["number"] for s in spec["slides"]]:errors.append("Review page set/order mismatch")
    if len({resolve(root,e.get("preview","")) for e in entries})!=len(entries):errors.append("Review preview paths must be unique")
    for entry in entries:
        tag=f"Slide {entry.get('number')}"
        preview=resolve(root,entry.get("preview",""))
        if not preview.is_file() or entry.get("sha256")!=digest(preview):errors.append(tag+": preview missing/stale")
        if any(entry.get("checks",{}).get(k) is not True for k in CHECKS) or not str(entry.get("observation","")).strip():
            errors.append(tag+": visual review incomplete or unresolved")
    return {"ok":not errors,"errors":errors,"scope":"Evidence completeness and freshness, not automated aesthetic judgment"}

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest="command",required=True)
    for command in ("prepare","check"):
        q=sub.add_parser(command);q.add_argument("--spec",required=True);q.add_argument("--pptx",required=True)
        if command=="prepare":q.add_argument("--previews",nargs="+",required=True);q.add_argument("--output",required=True)
        else:q.add_argument("--review",required=True)
    a=p.parse_args()
    if a.command=="prepare":
        prepare_review(a.spec,a.pptx,a.previews,a.output);print(json.dumps({"review":a.output,"status":"needs_human_review"}));return 0
    result=check_review(a.spec,a.pptx,a.review);print(json.dumps(result,ensure_ascii=False,indent=2));return 0 if result["ok"] else 1

if __name__=="__main__":
    try:raise SystemExit(main())
    except (ValueError,FileNotFoundError) as exc:raise SystemExit(str(exc))
