#!/usr/bin/env python3
"""Record answers; enforce template/style/materials order without repeated questions."""
from __future__ import annotations
import argparse
from pathlib import Path
from common import read_json,write_json,resolve
from filelock import FileLock

ANSWER_KEYS={"template","style","materials","topic","audience","slide_count","minutes","backend"}
def new_state():
    return {"version":1,"answers":{},"approvals":{"outline":False,"sample":False},"sample":None}

def load(project):
    p=Path(project)/"intake.json"
    return read_json(p) if p.exists() else new_state()

def next_action(state):
    a=state["answers"];t=a.get("template")
    if t is None:return {"action":"ask_template","question":"你是否有希望参考的PPT模板？"}
    if t=="none":
        if not a.get("style"):return {"action":"choose_style","source":"references/styles","choices":3}
    elif not isinstance(a.get("style"),dict) or not a["style"].get("inspected"):
        return {"action":"inspect_template","template":t,"scope":"visual style only unless user asks otherwise"}
    if a.get("materials") is None:return {"action":"ask_materials","question":"有没有图片、图标、图表、数据或文字素材？"}
    missing=[k for k in ("topic","audience") if not a.get(k)]
    if not a.get("slide_count") and not a.get("minutes"):missing.append("slide_count_or_minutes")
    if missing:return {"action":"clarify_brief","missing":missing}
    if not state["approvals"].get("outline"):return {"action":"review_outline"}
    b=a.get("backend",{})
    if not isinstance(b,dict) or not b.get("name") or not b.get("confirmed"):return {"action":"confirm_backend"}
    if not state.get("sample"):return {"action":"create_sample"}
    if not state["approvals"].get("sample"):return {"action":"review_sample","artifacts":state["sample"]}
    return {"action":"generate_full_deck"}

def require_ready(project,full=False):
    s=load(project);a=s["answers"]
    if a.get("template") is None:raise ValueError("Template question is unanswered")
    if not a.get("style"):raise ValueError("Style is not selected")
    if a["template"]!="none" and (not isinstance(a["style"],dict) or not a["style"].get("inspected")):
        raise ValueError("Template must be visually inspected before generation")
    if a.get("materials") is None:raise ValueError("Materials question is unanswered")
    if not a.get("topic") or not a.get("audience") or not (a.get("slide_count") or a.get("minutes")) or not s["approvals"].get("outline"):
        raise ValueError("Topic/audience/length/outline not confirmed")
    b=a.get("backend",{})
    if not isinstance(b,dict) or not b.get("name") or not b.get("confirmed"):raise ValueError("Backend not confirmed")
    if full and not s["approvals"].get("sample"):raise ValueError("Editable sample not approved")
    return s

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest="command",required=True)
    for cmd in ("init","next","update","approve","sample"):
        q=sub.add_parser(cmd);q.add_argument("--project",required=True)
        if cmd=="update":q.add_argument("--answers",required=True,help="JSON file with known answers")
        if cmd=="approve":q.add_argument("--stage",choices=["outline","sample"],required=True);q.add_argument("--artifact")
        if cmd=="sample":q.add_argument("--pptx",required=True);q.add_argument("--preview",required=True)
    args=p.parse_args();r=Path(args.project).resolve();r.mkdir(parents=True,exist_ok=True)
    with FileLock(str(r/".intake.lock")):
        state=load(r)
        if args.command=="update":
            answers=read_json(args.answers)
            if not isinstance(answers,dict) or set(answers)-ANSWER_KEYS:raise ValueError("Unknown intake answer keys")
            changed={k for k,v in answers.items() if state["answers"].get(k)!=v}
            if changed-{"backend"}:
                state["approvals"]={"outline":False,"sample":False};state["sample"]=None
            elif "backend" in changed:
                state["approvals"]["sample"]=False;state["sample"]=None
            state["answers"].update(answers)
        elif args.command=="approve":
            if args.stage=="outline":
                state["approvals"]["outline"]=False
                if next_action(state)["action"]!="review_outline":raise ValueError("Template/style/materials/topic must precede outline")
                if not args.artifact or not resolve(r,args.artifact).is_file():raise ValueError("Outline artifact missing")
                state["approvals"]["outline"]=True
                state["outline_artifact"]=str(resolve(r,args.artifact))
            else:
                require_ready(r)
                if not state.get("sample"):raise ValueError("Register editable PPTX and preview before approval")
                state["approvals"]["sample"]=True
        elif args.command=="sample":
            require_ready(r)
            paths={k:str(resolve(r,getattr(args,k))) for k in ("pptx","preview")}
            if any(not Path(v).is_file() for v in paths.values()):raise ValueError("Sample PPTX or preview missing")
            from pptx import Presentation
            from pptx.enum.shapes import MSO_SHAPE_TYPE
            from PIL import Image
            try:
                deck=Presentation(paths["pptx"])
                if len(deck.slides)!=1:
                    raise ValueError("Editable sample must contain exactly one slide")
                if not any(shape.shape_type==MSO_SHAPE_TYPE.TEXT_BOX and shape.has_text_frame and shape.text.strip()
                           for shape in deck.slides[0].shapes):
                    raise ValueError("Sample contains no non-empty native text boxes")
                with Image.open(paths["preview"]) as preview:
                    if min(preview.size)<100:raise ValueError("Sample preview is too small")
                    preview.verify()
            except Exception as exc:
                raise ValueError(f"Invalid editable sample or preview: {exc}") from exc
            state["sample"]=paths;state["approvals"]["sample"]=False
        if args.command!="next" or not (r/"intake.json").exists():write_json(r/"intake.json",state)
        import json
        print(json.dumps(next_action(state),ensure_ascii=False,indent=2))
    return 0
if __name__=="__main__":
    try:raise SystemExit(main())
    except (ValueError,FileNotFoundError) as e:raise SystemExit(str(e))
