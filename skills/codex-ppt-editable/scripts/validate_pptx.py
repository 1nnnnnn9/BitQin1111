#!/usr/bin/env python3
"""Validate native text, table values, notes, geometry and original image bytes."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from common import load_spec, resolve, check_assets, source_for_image
from assemble_editable_ppt import selected_slides, emu, sha

def validate(spec_path,pptx_path,numbers=None):
    path,spec=load_spec(spec_path);root=path.parent;slides=selected_slides(spec,numbers)
    prs=Presentation(str(pptx_path));errors=[]
    assets=check_assets(spec);canvas=spec.get("canvas",{"width":1280,"height":720})
    if len(prs.slides)!=len(slides):errors.append("Slide count mismatch")
    if abs(prs.slide_width-emu(canvas["width"]))>2 or abs(prs.slide_height-emu(canvas["height"]))>2:
        errors.append("Canvas mismatch")
    for slide,data in zip(prs.slides,slides):
        prefix=f"Slide {data['number']}: "
        names=[s.name for s in slide.shapes]
        if len(set(names))!=len(names):errors.append(prefix+"duplicate shape names")
        byname={s.name:s for s in slide.shapes}
        for obj in data.get("texts",[]):
            shape=byname.get(obj["name"])
            if shape is None or not shape.has_text_frame or shape.shape_type!=MSO_SHAPE_TYPE.TEXT_BOX:
                errors.append(prefix+f"not a native text box: {obj['name']}")
            elif shape.text!=obj["text"]:
                errors.append(prefix+f"text mismatch: {obj['name']}")
        for i,obj in enumerate(data.get("tables",[])):
            name=obj.get("name",f"表格_{i+1}");shape=byname.get(name)
            if shape is None or not shape.has_table:errors.append(prefix+"missing native table: "+name)
            else:
                values=[[c.text for c in row.cells] for row in shape.table.rows]
                if values!=obj["data"]:errors.append(prefix+"table data mismatch")
        expected=[("背景",resolve(root,data["background"]),{"fit":"cover"})]
        expected += [(obj.get("name",f"原图_{i+1}"),resolve(root,source_for_image(obj,assets)),obj) for i,obj in enumerate(data.get("images",[]))]
        for name,source,obj in expected:
            shape=byname.get(name)
            if shape is None or shape.shape_type!=MSO_SHAPE_TYPE.PICTURE:
                errors.append(prefix+"missing picture: "+name);continue
            import hashlib
            if hashlib.sha256(shape.image.blob).hexdigest()!=sha(source):
                errors.append(prefix+"source image bytes changed: "+name)
            from PIL import Image
            with Image.open(source) as im:
                ratio=im.width*(1-shape.crop_left-shape.crop_right)/(im.height*(1-shape.crop_top-shape.crop_bottom))
            if abs((shape.width/shape.height)/ratio-1)>.001:
                errors.append(prefix+"picture aspect distorted: "+name)
            if obj.get("fit","contain")=="contain":
                crop=obj.get("crop",[0,0,0,0])
                if any(abs(a-b)>.00002 for a,b in zip(crop,[shape.crop_left,shape.crop_top,shape.crop_right,shape.crop_bottom])):
                    errors.append(prefix+"unexpected crop: "+name)
        expected_notes=data.get("notes","")
        if data.get("sources"):expected_notes+="\n\n来源：\n"+"\n".join(data["sources"])
        if not slide.has_notes_slide or slide.notes_slide.notes_text_frame.text!=expected_notes:
            errors.append(prefix+"notes mismatch")
        for shape in slide.shapes:
            if min(shape.left,shape.top)<-2 or shape.left+shape.width>prs.slide_width+2 or shape.top+shape.height>prs.slide_height+2:
                errors.append(prefix+"out of canvas: "+shape.name)
    return {"ok":not errors,"slides":len(prs.slides),"errors":errors,
            "scope":"Object structure/content only; visual inspection still required."}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--spec",required=True)
    p.add_argument("--pptx",required=True);p.add_argument("--slides",nargs="+",type=int);p.add_argument("--report")
    a=p.parse_args();result=validate(a.spec,a.pptx,a.slides)
    if a.report:
        from common import write_json
        write_json(a.report,result)
    print(json.dumps(result,ensure_ascii=False,indent=2));return 0 if result["ok"] else 1
if __name__=="__main__":raise SystemExit(main())
