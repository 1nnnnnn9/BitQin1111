#!/usr/bin/env python3
"""Assemble generated backgrounds with native editable PowerPoint objects. MIT."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from common import load_spec, resolve, check_box, check_assets, source_for_image, read_json, write_json
from intake import require_ready, sample_only_selection, sample_numbers
from visual_planning import validate_plans

def emu(px):
    return Inches(float(px)/96)

def rgb(value):
    return RGBColor.from_string(str(value).lstrip("#"))

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def selected_slides(spec, numbers=None):
    slides=spec["slides"]
    if numbers is None:
        return slides
    missing=set(numbers)-{s["number"] for s in slides}
    if missing:raise ValueError(f"Unknown slides: {missing}")
    return [s for s in slides if s["number"] in numbers]

def verify_backgrounds(root, slides, spec):
    jobs=read_json(root/"slide_jobs.json")
    by_number={j["number"]:j for j in jobs["slides"]}
    for s in slides:
        j=by_number.get(s["number"],{})
        result=j.get("result") or {}
        path=resolve(root,s["background"])
        if j.get("status") not in ("recorded","accepted") or not result.get("backend_used"):
            raise ValueError(f"Slide {s['number']}: background generation not recorded")
        if resolve(root,result.get("final_image","")) != path or result.get("final_image_sha256") != sha(path):
            raise ValueError(f"Slide {s['number']}: background hash/path differs from recorded output")
        if not result.get("sample_generation_method_matched"):
            raise ValueError(f"Slide {s['number']}: backend provenance not matched")
        if jobs.get("selected_backend") != spec.get("backend"):
            raise ValueError("Recorded backend does not match spec")

def _unique(name, names):
    if not isinstance(name,str) or not name.strip() or name in names:
        raise ValueError(f"Missing or duplicate object name: {name}")
    names.add(name)
    return name

def add_image(slide, path, item, canvas, name):
    x,y,w,h=check_box(item["box"],canvas,name)
    crop=list(item.get("crop",[0,0,0,0]))
    if len(crop)!=4 or any(v<0 or v>=1 for v in crop) or crop[0]+crop[2]>=1 or crop[1]+crop[3]>=1:
        raise ValueError(f"{name}: invalid crop")
    with Image.open(path) as im:
        iw,ih=im.size
    left,top,right,bottom=crop
    visible_w,visible_h=iw*(1-left-right),ih*(1-top-bottom)
    source_ratio=visible_w/visible_h;target_ratio=w/h
    fit=item.get("fit","contain")
    if fit=="contain":
        if source_ratio>target_ratio:
            hh=w/source_ratio;y+=(h-hh)/2;h=hh
        else:
            ww=h*source_ratio;x+=(w-ww)/2;w=ww
    elif fit=="cover":
        if source_ratio>target_ratio:
            keep=visible_h*target_ratio/iw;extra=(1-left-right-keep)/2;left+=extra;right+=extra
        else:
            keep=visible_w/target_ratio/ih;extra=(1-top-bottom-keep)/2;top+=extra;bottom+=extra
    else:
        raise ValueError(f"{name}: fit must be contain or cover")
    pic=slide.shapes.add_picture(str(path),emu(x),emu(y),width=emu(w),height=emu(h))
    pic.crop_left,pic.crop_top,pic.crop_right,pic.crop_bottom=left,top,right,bottom
    pic.name=name
    return pic

def style_text(frame, obj, font):
    frame.word_wrap=True
    margin=emu(obj.get("margin",0))
    frame.margin_left=frame.margin_right=frame.margin_top=frame.margin_bottom=margin
    frame.vertical_anchor={"top":MSO_ANCHOR.TOP,"middle":MSO_ANCHOR.MIDDLE,"bottom":MSO_ANCHOR.BOTTOM}[obj.get("vertical_align","top")]
    for p in frame.paragraphs:
        p.alignment={"left":PP_ALIGN.LEFT,"center":PP_ALIGN.CENTER,"right":PP_ALIGN.RIGHT}[obj.get("align","left")]
        p.space_before=Pt(0);p.space_after=Pt(obj.get("paragraph_space",0)*.75)
        p.line_spacing=float(obj.get("line_spacing",1.15))
        for run in p.runs:
            run.font.name=obj.get("font",font)
            run.font.size=Pt(obj.get("font_size",28)*.75)
            run.font.bold=obj.get("bold",False);run.font.italic=obj.get("italic",False)
            run.font.color.rgb=rgb(obj.get("color","#163D3A"))
            # Set East Asian font explicitly; fallback remains portable if that font is absent.
            from pptx.oxml.xmlchemy import OxmlElement
            east=OxmlElement("a:ea");east.set("typeface",obj.get("font",font))
            run._r.get_or_add_rPr().append(east)

def build(spec_path, output, numbers=None, force=False):
    path,spec=load_spec(spec_path);root=path.parent
    slides=selected_slides(spec,numbers)
    state=require_ready(root,full=not sample_only_selection(spec,numbers))
    if state.get("version",1)>=2:
        if spec.get("schema_version",1)<2:raise ValueError("New projects require schema_version 2")
        if spec.get("visual_preference")!=state["answers"].get("visual_preference"):
            raise ValueError("Spec visual preference differs from confirmed intake")
        if numbers is None and (state.get("sample") or {}).get("slides")!=sample_numbers(spec):
            raise ValueError("Approved sample set differs from deck sample_slides")
    validate_plans(spec)
    assets=check_assets(spec)
    verify_backgrounds(root,slides,spec)
    output=Path(output).expanduser().resolve()
    if output.exists() and not force:raise ValueError("Output exists; use --force to replace")
    canvas=spec.get("canvas",{"width":1280,"height":720})
    font=spec.get("font","Aptos")
    prs=Presentation();prs.slide_width=emu(canvas["width"]);prs.slide_height=emu(canvas["height"])
    prs.core_properties.title=spec.get("title","Editable presentation")
    prs.core_properties.subject="Generated non-text backgrounds with native editable text"
    manifest={"version":1,"slides":[],"canvas":canvas}
    for data in slides:
        slide=prs.slides.add_slide(prs.slide_layouts[6]);names=set()
        background=resolve(root,data["background"])
        with Image.open(background) as image:
            ratio=image.width/image.height
        if abs(ratio/(canvas["width"]/canvas["height"])-1)>.015:
            raise ValueError(f"Slide {data['number']}: background aspect ratio differs from canvas")
        add_image(slide,background,{"box":[0,0,canvas["width"],canvas["height"]],"fit":"cover"},canvas,_unique("背景",names))
        for obj in data.get("texts",[]):
            name=_unique(obj["name"],names)
            x,y,w,h=check_box(obj["box"],canvas,name)
            if not isinstance(obj["text"],str) or "\\n" in obj["text"]:
                raise ValueError(f"{name}: text needs strings with real newlines")
            shape=slide.shapes.add_textbox(emu(x),emu(y),emu(w),emu(h));shape.name=name
            shape.text_frame.text=obj["text"]
            style_text(shape.text_frame,obj,font)
        for i,obj in enumerate(data.get("images",[])):
            name=_unique(obj.get("name",f"原图_{i+1}"),names)
            add_image(slide,resolve(root,source_for_image(obj,assets)),obj,canvas,name)
        for i,obj in enumerate(data.get("tables",[])):
            name=_unique(obj.get("name",f"表格_{i+1}"),names)
            x,y,w,h=check_box(obj["box"],canvas,name);rows=obj["data"]
            if not rows or not rows[0] or any(len(r)!=len(rows[0]) for r in rows):
                raise ValueError(f"{name}: data must be a non-empty rectangular array")
            if any(not isinstance(v,str) for r in rows for v in r):
                raise ValueError(f"{name}: preserve values as strings")
            shape=slide.shapes.add_table(len(rows),len(rows[0]),emu(x),emu(y),emu(w),emu(h));shape.name=name
            table=shape.table
            widths=obj.get("column_widths",[1]*len(rows[0]))
            if len(widths)!=len(rows[0]) or min(widths)<=0:raise ValueError("Invalid column_widths")
            for col,weight in zip(table.columns,widths):
                col.width=emu(w*weight/sum(widths))
            for ri,row in enumerate(rows):
                for ci,value in enumerate(row):
                    cell=table.cell(ri,ci);cell.text=value
                    header=ri<obj.get("header_rows",1)
                    cell.fill.solid();cell.fill.fore_color.rgb=rgb(obj.get("header_fill","#163D3A") if header else obj.get("cell_fill","#F1F7F6"))
                    style_text(cell.text_frame,{"font_size":obj.get("font_size",24),"bold":header,
                        "color":obj.get("header_color","#FFFFFF") if header else obj.get("color","#163D3A"),
                        "margin":obj.get("margin",10),"vertical_align":"middle"},font)
        notes=data.get("notes","")
        sources=data.get("sources",[])
        if sources:notes+="\n\n来源：\n"+"\n".join(sources)
        slide.notes_slide.notes_text_frame.text=notes
        manifest["slides"].append({"number":data["number"],"native_texts":len(data.get("texts",[])),
                                  "tables":len(data.get("tables",[])),"background_sha256":sha(background)})
    output.parent.mkdir(parents=True,exist_ok=True)
    prs.save(str(output));write_json(output.with_suffix(".build.json"),manifest)
    return manifest

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--spec",required=True);p.add_argument("--output",required=True)
    p.add_argument("--slides",nargs="+",type=int);p.add_argument("--force",action="store_true")
    a=p.parse_args();print(json.dumps(build(a.spec,a.output,a.slides,a.force),ensure_ascii=False,indent=2))
if __name__=="__main__":
    try:main()
    except (ValueError,FileNotFoundError) as exc:raise SystemExit(str(exc))
