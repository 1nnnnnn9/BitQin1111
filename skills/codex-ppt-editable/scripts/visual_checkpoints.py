#!/usr/bin/env python3
"""Stop at each new visual family/variant until a human accepts its representative. MIT."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import uuid
from filelock import FileLock
from common import read_json,write_json,load_spec,resolve

def enabled(state):
    return state.get("version",1)>=2 and state.get("visual_checkpoints",{}).get("enabled",False)

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode()).hexdigest()

def file_sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def context(spec):
    return digest({k:spec.get(k) for k in ("canvas","font","style","visual_preference","diagram_style","backend","background_generation_method")})

def visual_key(slide):
    plan=slide.get("visual_plan",{});form=plan.get("form","illustration")
    families={form}
    if slide.get("tables"):families.add("table")  # Native tables cannot hide under a flowchart label.
    if any(i.get("role") not in {"logo","brand","background"} for i in slide.get("images",[])):families.add("source_figure")
    shape="standard"
    if form=="flowchart":
        incoming={};outgoing={}
        for e in plan.get("relations",[]):
            incoming[e.get("to")]=incoming.get(e.get("to"),0)+1
            outgoing[e.get("from")]=outgoing.get(e.get("from"),0)+1
        shape="grouped" if plan.get("groups") else "branched" if any(n>1 for n in [*incoming.values(),*outgoing.values()]) else "linear"
    if slide.get("tables"):
        table_layouts=[]
        for table in slide["tables"]:
            rows=table.get("data",[]);columns=len(rows[0]) if rows else 0
            density="short" if len(rows)<=6 else "medium" if len(rows)<=12 else "dense"
            treatment={k:table.get(k) for k in ("header_fill","header_color","cell_fill","color","font","header_rows","column_widths")}
            treatment["type_size"]="small" if table.get("font_size",24)<22 else "regular"
            table_layouts.append(f"{columns}col-{density}-"+digest(treatment)[:10])
        shape+="/"+"+".join(table_layouts)
    if form=="data_chart":shape+="/"+str(plan.get("chart_type","unspecified"))
    if "source_figure" in families:shape+="/"+("multi-image" if len(slide.get("images",[]))>1 else "single-image")
    variant=plan.get("visual_variant",slide.get("visual_variant","standard"))
    if not isinstance(variant,str) or not variant.strip():raise ValueError("visual_variant must be a non-empty string")
    return "+".join(sorted(families))+"::"+shape+"::"+variant

def slide_digest(slide):
    return digest({k:slide.get(k) for k in ("background","texts","tables","images","visual_plan","visual_variant","scene_brief","style_reference_images")})

def checkpoint_valid(record,spec):
    if not record or record.get("status")!="approved" or record.get("context")!=context(spec):return False
    page=next((s for s in spec["slides"] if s["number"]==record.get("slide")),None)
    if not page or record.get("slide_digest")!=slide_digest(page):return False
    for key in ("pptx","preview","background"):
        path=Path(record.get(key,""))
        if not path.is_file() or record.get(key+"_sha256")!=file_sha(path):return False
    source=Path(record.get("source_background",""))
    if not source.is_file() or file_sha(source)!=record.get("background_sha256"):return False
    return True

def frontier(spec,state):
    """Only the approved prefix plus ONE next representative may be produced."""
    approvals=state.get("visual_checkpoints",{}).get("approvals",{})
    prefix=[]
    for slide in spec["slides"]:
        key=visual_key(slide)
        if checkpoint_valid(approvals.get(key),spec):prefix.append(slide["number"])
        else:return prefix,{"slide":slide["number"],"visual_key":key,"section":slide.get("section")}
    return prefix,None

def next_visual_action(spec,state):
    prefix,pending=frontier(spec,state)
    if not pending:return {"action":"generate_approved_visuals","slides":prefix,"all_visual_families_approved":True}
    draft=state["visual_checkpoints"].get("drafts",{}).get(pending["visual_key"],{})
    action="create_visual_checkpoint"
    if draft.get("status")=="pending":action="review_visual_checkpoint"
    elif draft.get("status")=="rejected":action="choose_visual_revision"
    return {"action":action,**pending,"approved_prefix":prefix,"artifacts":draft or None,
            "instruction":"Show this representative and wait for the user's decision before producing later pages."}

def assert_selection(spec,state,numbers,checkpoint_only=False):
    if not enabled(state) or not state["approvals"].get("sample"):return
    prefix,pending=frontier(spec,state)
    if numbers is None:
        if pending:raise ValueError(f"Visual checkpoint required at slide {pending['slide']} ({pending['visual_key']}); initial sample approval does not approve the whole deck")
        return
    if checkpoint_only:
        if not pending or numbers!=[pending["slide"]]:raise ValueError("Only the next unapproved visual representative may be prepared as a checkpoint")
        return
    if pending and numbers==[pending["slide"]]:return  # Assemble its single-page editable preview.
    samples=(state.get("sample") or {}).get("slides",[])
    if not set(numbers)<=set(prefix+samples):raise ValueError("Later visual pages are blocked until the current checkpoint is approved")

def assert_final_approved(spec,state):
    if enabled(state) and not state["approvals"].get("sample"):raise ValueError("Initial editable samples are still awaiting user approval")
    assert_selection(spec,state,None)

def assert_generation_allowed(root,number):
    root=Path(root)
    if not (root/"intake.json").is_file():return
    state=read_json(root/"intake.json")
    if not enabled(state):return
    _,spec=load_spec(root/"deck_spec.json")
    if not state["approvals"].get("sample"):
        from intake import sample_numbers
        allowed=sample_numbers(spec)
    else:
        prefix,pending=frontier(spec,state)
        allowed=prefix+(state.get("sample") or {}).get("slides",[])+([pending["slide"]] if pending else [])
    if number not in allowed:raise ValueError(f"Slide {number}: blocked by the current visual checkpoint; ask the user before producing later pages")

def generation_selection(spec,state,checkpoint_only=None):
    if not enabled(state):
        if checkpoint_only is not None:raise ValueError("Enable visual checkpoints first")
        return None
    prefix,pending=frontier(spec,state)
    if checkpoint_only is not None:
        assert_selection(spec,state,[checkpoint_only],True);return [checkpoint_only]
    if not prefix and pending:raise ValueError(f"Create the next representative with --checkpoint-only {pending['slide']}, then ask the user")
    return prefix

def anchor_images(spec,state,slide):
    if not enabled(state) or not state["approvals"].get("sample"):return []
    approvals=state["visual_checkpoints"].get("approvals",{})
    preferred=approvals.get(visual_key(slide))
    records=([preferred] if preferred else [])+list(approvals.values())
    for record in records:
        if checkpoint_valid(record,spec):return [record["preview"]]
    return []

def _snapshot(root,spec,slide,pptx,preview):
    from PIL import Image
    for p in (pptx,preview,resolve(root,slide["background"])):
        if not Path(p).is_file():raise ValueError("Checkpoint artifact missing: "+str(p))
    with Image.open(preview) as image:
        if min(image.size)<100:raise ValueError("Checkpoint preview is too small")
        image.verify()
    folder=root/"visual_checkpoints"/uuid.uuid4().hex;folder.mkdir(parents=True)
    record={"slide":slide["number"],"visual_key":visual_key(slide),"context":context(spec),"slide_digest":slide_digest(slide),
            "source_background":str(resolve(root,slide["background"]))}
    for key,source in (("pptx",pptx),("preview",preview),("background",resolve(root,slide["background"]))):
        target=folder/(key+Path(source).suffix);shutil.copy2(source,target)
        record[key]=str(target);record[key+"_sha256"]=file_sha(target)
    return record

def seed_samples(root,spec,state):
    if not enabled(state):return
    sample=state.get("sample") or {};nums=sample.get("slides",[]);previews=sample.get("previews",[])
    if len(nums)!=len(previews):raise ValueError("Sample slide/preview mapping missing for visual checkpoints")
    if not nums:raise ValueError("Approved sample evidence missing; restore/register its page mapping first")
    approvals=state["visual_checkpoints"].setdefault("approvals",{})
    for n,p in zip(nums,previews):
        slide=next(s for s in spec["slides"] if s["number"]==n)
        record=_snapshot(root,spec,slide,resolve(root,sample["pptx"]),resolve(root,p));record["status"]="approved"
        approvals[visual_key(slide)]=record

def clear_decisions(state):
    if enabled(state):state["visual_checkpoints"]={"enabled":True,"approvals":{},"drafts":{}}

def invalidate_representative(state,number):
    if not enabled(state):return
    cp=state["visual_checkpoints"]
    for key,record in list(cp.get("approvals",{}).items()):
        if record.get("slide")==number:cp["approvals"].pop(key)
    for draft in cp.get("drafts",{}).values():
        if draft.get("slide")==number and draft.get("status")=="pending":draft["status"]="needs_regeneration"

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest="command",required=True)
    for command in ("enable","next","register","approve","reject","choose"):
        q=sub.add_parser(command);q.add_argument("--project",required=True)
        if command not in ("enable","next"):q.add_argument("--slide",type=int,required=True)
        if command=="register":q.add_argument("--pptx",required=True);q.add_argument("--preview",required=True)
        if command=="reject":q.add_argument("--reason",required=True);q.add_argument("--options",required=True)
        if command=="choose":q.add_argument("--option",required=True)
    a=p.parse_args();root=Path(a.project).resolve()
    with FileLock(str(root/".intake.lock")):
        state=read_json(root/"intake.json");_,spec=load_spec(root/"deck_spec.json")
        if a.command=="enable":
            if state.get("version",1)<2:raise ValueError("Upgrade legacy v1 spec/intake before enabling visual checkpoints")
            if not enabled(state):
                state["visual_checkpoints"]={"enabled":True,"approvals":{},"drafts":{}}
                if state["approvals"].get("sample"):seed_samples(root,spec,state)
        elif not enabled(state):raise ValueError("Visual checkpoints are not enabled")
        if a.command not in ("enable","next"):
            if not state["approvals"].get("sample"):raise ValueError("Initial editable samples must be approved first")
            slide=next((s for s in spec["slides"] if s["number"]==a.slide),None)
            if slide is None:raise ValueError("Unknown checkpoint slide")
            key=visual_key(slide);cp=state["visual_checkpoints"];drafts=cp.setdefault("drafts",{})
            _,pending=frontier(spec,state)
            if not pending or pending["slide"]!=a.slide:raise ValueError("Finish the earliest unapproved visual checkpoint first")
            previous=drafts.get(key,{})
            if a.command=="register":
                from validate_pptx import validate
                from pptx import Presentation
                from pptx.enum.shapes import MSO_SHAPE_TYPE
                pptx=resolve(root,a.pptx);preview=resolve(root,a.preview)
                checked=validate(root/"deck_spec.json",pptx,[a.slide])
                if not checked["ok"]:raise ValueError("Checkpoint PPTX does not match the representative: "+str(checked["errors"]))
                deck=Presentation(pptx)
                if not any(s.shape_type==MSO_SHAPE_TYPE.TEXT_BOX and s.text.strip() for s in deck.slides[0].shapes):raise ValueError("Checkpoint needs native text")
                if previous.get("status") in {"rejected","revision_selected"} and previous.get("pptx_sha256")==file_sha(pptx) and previous.get("preview_sha256")==file_sha(preview):
                    raise ValueError("Rejected preview is unchanged; implement the selected revision and render again")
                record=_snapshot(root,spec,slide,pptx,preview);record["status"]="pending"
                if previous.get("selected_option"):record["selected_option"]=previous["selected_option"]
                drafts[key]=record
            elif a.command=="approve":
                if previous.get("status")!="pending":raise ValueError("Register a revised editable preview before approval")
                test={**previous,"status":"approved"}
                if not checkpoint_valid(test,spec):raise ValueError("Checkpoint is stale; register the current preview again")
                cp.setdefault("approvals",{})[key]=test;drafts.pop(key,None)
            elif a.command=="reject":
                if previous.get("status")!="pending":raise ValueError("No pending checkpoint to reject")
                options=read_json(resolve(root,a.options))
                if (not isinstance(options,list) or not 2<=len(options)<=3 or any(not all(isinstance(o.get(k),str) and o[k].strip() for k in ("id","label","description")) for o in options)
                    or len({o["id"] for o in options})!=len(options) or not a.reason.strip()):raise ValueError("Provide a reason and 2–3 distinct concrete revision options")
                previous.update(status="rejected",reason=a.reason,options=options)
            elif a.command=="choose":
                if previous.get("status")!="rejected":raise ValueError("No rejected checkpoint with alternatives")
                if a.option not in {o["id"] for o in previous["options"]}:raise ValueError("Unknown revision option")
                previous.update(status="revision_selected",selected_option=a.option)
        if a.command!="next":write_json(root/"intake.json",state)
        print(json.dumps(next_visual_action(spec,state),ensure_ascii=False,indent=2))
    return 0

if __name__=="__main__":
    try:raise SystemExit(main())
    except (ValueError,FileNotFoundError) as exc:raise SystemExit(str(exc))
