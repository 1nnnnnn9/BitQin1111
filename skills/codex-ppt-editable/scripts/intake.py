#!/usr/bin/env python3
"""Record answers; enforce template/style/materials order without repeated questions."""
from __future__ import annotations
import argparse
from pathlib import Path
from common import read_json,write_json,resolve
from filelock import FileLock

VISUAL_MODES={"schematic","realistic","mixed"}
ANSWER_KEYS={"template","style","materials","visual_preference","topic","audience","slide_count","minutes","backend"}
def new_state():
    return {"version":2,"answers":{},"approvals":{"outline":False,"sample":False},"sample":None}

def sample_numbers(spec):
    """Read v2 sample sets while keeping the v1 scalar contract."""
    numbers=spec.get("sample_slides")
    if numbers is None:
        numbers=[spec.get("sample_slide",spec["slides"][0]["number"])]
    valid={s["number"] for s in spec["slides"]}
    expected=min(2,len(valid)) if spec.get("schema_version",1)>=2 else 1
    if (not isinstance(numbers,list) or len(numbers)!=expected
            or any(type(n) is not int or n not in valid for n in numbers)
            or len(set(numbers))!=len(numbers)):
        raise ValueError(f"Expected {expected} distinct existing sample slide numbers")
    if numbers!=[s["number"] for s in spec["slides"] if s["number"] in numbers]:
        raise ValueError("sample_slides must follow spec slide order")
    return numbers

def sample_only_selection(spec,numbers):
    return numbers is not None and set(numbers)<=set(sample_numbers(spec))

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
    if state.get("version",1)>=2 and a.get("visual_preference") not in VISUAL_MODES:
        return {"action":"choose_visual_preference","question":"配图希望哪一种居多？", "options":[
            {"value":"schematic","label":"简略示意图为主"},
            {"value":"realistic","label":"写实／三维图为主"},
            {"value":"mixed","label":"按内容混合"}]}
    missing=[k for k in ("topic","audience") if not a.get(k)]
    if not a.get("slide_count") and not a.get("minutes"):missing.append("slide_count_or_minutes")
    if missing:return {"action":"clarify_brief","missing":missing}
    if not state["approvals"].get("outline"):return {"action":"review_outline"}
    b=a.get("backend",{})
    if not isinstance(b,dict) or not b.get("name") or not b.get("confirmed"):return {"action":"confirm_backend"}
    if not state.get("sample"):return {"action":"create_sample","count":min(2,a.get("slide_count") or 2) if state.get("version",1)>=2 else 1}
    if not state["approvals"].get("sample"):return {"action":"review_sample","artifacts":state["sample"]}
    return {"action":"generate_full_deck"}

def require_ready(project,full=False):
    s=load(project);a=s["answers"]
    if a.get("template") is None:raise ValueError("Template question is unanswered")
    if not a.get("style"):raise ValueError("Style is not selected")
    if a["template"]!="none" and (not isinstance(a["style"],dict) or not a["style"].get("inspected")):
        raise ValueError("Template must be visually inspected before generation")
    if a.get("materials") is None:raise ValueError("Materials question is unanswered")
    if s.get("version",1)>=2 and a.get("visual_preference") not in VISUAL_MODES:
        raise ValueError("Visual preference question is unanswered")
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
        if cmd=="sample":
            q.add_argument("--pptx",required=True)
            q.add_argument("--preview",required=True,nargs="+")
            q.add_argument("--slides",nargs="+",type=int)
    args=p.parse_args();r=Path(args.project).resolve();r.mkdir(parents=True,exist_ok=True)
    with FileLock(str(r/".intake.lock")):
        state=load(r)
        if args.command=="update":
            answers=read_json(args.answers)
            if not isinstance(answers,dict) or set(answers)-ANSWER_KEYS:raise ValueError("Unknown intake answer keys")
            if "visual_preference" in answers and answers["visual_preference"] not in VISUAL_MODES:
                raise ValueError("visual_preference must be schematic, realistic or mixed")
            changed={k for k,v in answers.items() if state["answers"].get(k)!=v}
            if changed-{"backend"}:
                state["approvals"]={"outline":False,"sample":False};state["sample"]=None
            elif "backend" in changed:
                state["approvals"]["sample"]=False;state["sample"]=None
            state["answers"].update(answers)
        elif args.command=="approve":
            if args.stage=="outline":
                state["approvals"]["outline"]=False
                if next_action(state)["action"]!="review_outline":raise ValueError("Template/style/materials/visual preference/topic must precede outline")
                if not args.artifact or not resolve(r,args.artifact).is_file():raise ValueError("Outline artifact missing")
                state["approvals"]["outline"]=True
                state["outline_artifact"]=str(resolve(r,args.artifact))
            else:
                require_ready(r)
                if not state.get("sample"):raise ValueError("Register editable PPTX and preview before approval")
                state["approvals"]["sample"]=True
        elif args.command=="sample":
            require_ready(r)
            paths={"pptx":str(resolve(r,args.pptx)),"previews":[str(resolve(r,v)) for v in args.preview]}
            if any(not Path(v).is_file() for v in [paths["pptx"],*paths["previews"]]):raise ValueError("Sample PPTX or preview missing")
            from pptx import Presentation
            from pptx.enum.shapes import MSO_SHAPE_TYPE
            from PIL import Image
            try:
                deck=Presentation(paths["pptx"])
                if state.get("version",1)>=2:
                    from common import load_spec
                    _,spec=load_spec(r/"deck_spec.json")
                    expected=sample_numbers(spec)
                    if args.slides!=expected:raise ValueError("--slides must match sample_slides order in deck_spec.json")
                    paths["slides"]=expected
                    from validate_pptx import validate
                    checked=validate(r/"deck_spec.json",paths["pptx"],expected)
                    if not checked["ok"]:raise ValueError("Sample content differs from declared slides: "+"; ".join(checked["errors"]))
                else:expected=[1]
                if len(deck.slides)!=len(expected) or len(paths["previews"])!=len(expected):
                    raise ValueError(f"Editable sample needs {len(expected)} slides and matching previews")
                if len(set(paths["previews"]))!=len(expected):raise ValueError("Each sample needs its own preview")
                for slide,preview_path in zip(deck.slides,paths["previews"]):
                    if not any(shape.shape_type==MSO_SHAPE_TYPE.TEXT_BOX and shape.has_text_frame and shape.text.strip()
                               for shape in slide.shapes):
                        raise ValueError("Every sample slide needs non-empty native text boxes")
                    with Image.open(preview_path) as preview:
                        if min(preview.size)<100:raise ValueError("Sample preview is too small")
                        preview.verify()
                if state.get("version",1)<2:paths={"pptx":paths["pptx"],"preview":paths["previews"][0]}
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
