#!/usr/bin/env python3
"""Prepare text-free image jobs; never render slide art in code."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from filelock import FileLock
from common import load_spec, check_box
from intake import require_ready, sample_numbers
from visual_planning import validate_plans, MODES, prompt_plan
from style_contract import visual_style
from diagram_style import engineering_contract
from visual_checkpoints import enabled, generation_selection, anchor_images, visual_key
from slide_run_state import read_json, write_json, now_iso, update_jobs_run_status

def prepare(spec_path, sample_only=None, checkpoint_only=None):
    path, spec = load_spec(spec_path)
    root = path.parent
    if sample_only is not None and checkpoint_only is not None:raise ValueError("Use either --sample-only or --checkpoint-only")
    state = require_ready(root, full=sample_only is None)
    modern=state.get("version",1)>=2
    if modern and spec.get("schema_version",1)<2:
        raise ValueError("New projects require schema_version 2 with per-slide visual plans")
    validate_plans(spec)
    if modern and spec.get("visual_preference")!=state["answers"].get("visual_preference"):
        raise ValueError("Spec visual preference differs from confirmed intake")
    samples=sample_numbers(spec)
    if modern and sample_only is None and (state.get("sample") or {}).get("slides")!=samples:
        raise ValueError("Approved sample set differs from deck sample_slides")
    backend = state["answers"]["backend"]["name"]
    if spec.get("backend", backend) != backend:
        raise ValueError("Spec backend differs from confirmed intake backend")
    canvas = spec.get("canvas", {"width":1280,"height":720})
    selection=[sample_only] if isinstance(sample_only,int) else sample_only
    if selection is not None and (not selection or len(set(selection))!=len(selection) or not set(selection)<=set(samples)):
        raise ValueError("Before sample approval only declared sample_slides may be prepared")
    if state["approvals"].get("sample") and modern and (state.get("sample") or {}).get("slides")!=samples:
        raise ValueError("Declared initial samples differ from the approved sample set")
    if sample_only is None and enabled(state):selection=generation_selection(spec,state,checkpoint_only)
    elif checkpoint_only is not None:raise ValueError("Enable visual checkpoints before --checkpoint-only")
    selected = [s for s in spec["slides"] if selection is None or s["number"] in selection]
    if not selected:
        raise ValueError("Sample slide does not exist")
    with FileLock(str(root/".slide_jobs.json.lock")):
        prior = read_json(root/"slide_jobs.json", default={})
        old = {s["number"]:s for s in prior.get("slides", [])}
        entries = []
        for slide in selected:
            n = slide["number"]
            sid = f"slide_{n:02d}"
            zones = []
            for kind in ("texts","images","tables"):
                for i, obj in enumerate(slide.get(kind, [])):
                    box = check_box(obj["box"], canvas, f"{sid}/{kind}/{i}")
                    zones.append({"box":box,"purpose":kind,"object":obj.get("name",f"{kind}_{i+1}")})
            visual_instructions=""
            diagram_contract=engineering_contract(spec,slide) if spec.get("schema_version",1)>=2 else None
            if spec.get("schema_version",1)>=2:
                visual_instructions=(
                    "\nDesign this as a complete polished codex-ppt slide, with the selected style's composition, meaningful diagrams, layered visual hierarchy and balanced image treatment. "
                    "Only the typography is deferred to native PowerPoint. Blank text areas must not turn the whole slide into a plain white master, sparse boxes, or a repeated grid. "
                    "A reserved text rectangle is a low-detail typography surface, not a mandatory visible white box; preserve suitable colored panels, grouping, textures and subject-relevant visual structure around it. "
                    "\nIllustration preference: "+MODES[spec["visual_preference"]]
                    +"\nExplanatory visual plan: "+json.dumps(prompt_plan(slide["visual_plan"]),ensure_ascii=False)
                    +"\nFollow relationship directions. Node boxes guide placement, not a requirement that every object be a generic rectangular module. IDs are instructions only: never print them. "
                    "Draw node borders around quiet label interiors, not over reserved label rectangles. "
                    "Use arrows when required by the plan. The plan takes precedence over a conflicting supplemental brief. "
                    "Do not replace a process/layout/system diagram with an ornamental machine portrait or an empty master. "
                    "If this is a data chart, reproduce the supplied marks and proportions exactly, leaving all typography for native labels."
                )
                if diagram_contract:
                    visual_instructions+=("\nDiagram treatment (takes precedence over conflicting visual embellishment in the diagram field): "
                        +json.dumps(diagram_contract,ensure_ascii=False))
            prompt = (
                "Create a professional slide BACKGROUND AND NON-TEXT ILLUSTRATION ONLY. "
                f"Landscape canvas aspect {canvas['width']}:{canvas['height']}. "
                "ABSOLUTELY NO TEXT: no titles, words, letters, numbers, labels, pseudo-writing, "
                "watermarks, signatures, legends or axes. Do not draw placeholder text or white cover-up boxes. "
                "The actual editable words and supplied original figures will be placed afterward in PowerPoint. "
                "Keep every reserved rectangle genuinely quiet and empty with a clean low-detail surface. "
                "Place all illustration outside those rectangles; do not invent experimental data. "
                "\nVisual style (ignore any legacy instruction to draw text): "
                + json.dumps(visual_style(spec.get("style",{})) if spec.get("schema_version",1)>=2 else spec.get("style",{}),ensure_ascii=False)
                + "\nIllustration brief: " + slide.get("scene_brief","Minimal restrained visual background.")
                + visual_instructions
                + "\nReserved rectangles in 96-DPI canvas coordinates: " + json.dumps(zones,ensure_ascii=False)
            )
            if spec.get("schema_version",1)>=2 and slide["visual_plan"]["form"]=="data_chart":
                prompt=prompt.replace("legends or axes.","legend text or axis text.")
            inputs = list(slide.get("style_reference_images", []))
            existing=old.get(n)
            stored_job={}
            if enabled(state) and existing and existing.get("status")!="pending":
                stored_job=read_json(root/existing.get("job",f"prompts/{sid}.json"))
            anchors=(anchor_images(spec,state,slide) if not existing or existing.get("status")=="pending"
                     else stored_job.get("visual_checkpoint",{}).get("anchor_images",[]))
            for anchor in anchors:
                if anchor not in inputs:inputs.append(anchor)
            if anchors:
                prompt+=("\nAn approved completed page is supplied as a visual anchor. Preserve its overall palette, title hierarchy, linework and visual language while adapting this page's structure. "
                    "Do not copy its words, figures, data or table cells; all new typography/tables are assembled natively. "
                    "A new visual family or a markedly different layout still requires a human checkpoint, even when the palette is the same.")
            for inp in inputs:
                if not (root/inp).is_file():
                    raise FileNotFoundError(f"Missing style reference: {inp}")
            job = {
                "slide":n,"slide_id":sid,"prompt":prompt,
                "out":slide.get("background", f"origin_image/{sid}.png"),
                "input_images":inputs,"expected_backend":backend,
                "sample_generation_method":spec.get("background_generation_method",{}),
                "background_contract":{"text_free":True,"reserved_zones":zones},
            }
            if diagram_contract:job["diagram_contract"]=diagram_contract
            if enabled(state) and (not existing or existing.get("status")=="pending"):
                job["visual_checkpoint"]={"visual_key":visual_key(slide),"anchor_images":anchors,
                    "representative":checkpoint_only==n}
            elif "visual_checkpoint" in stored_job:job["visual_checkpoint"]=stored_job["visual_checkpoint"]
            out = (root/job["out"]).resolve()
            out.relative_to(root)
            job_ref = f"prompts/{sid}.json"
            previous = old.get(n)
            if previous and previous.get("status") != "pending":
                old_job = read_json(root/job_ref)
                if old_job != job:
                    # The user approved a complete editable sample after native text
                    # placement was refined. Keep its original generation prompt and
                    # output provenance; only assembly rectangles may differ.
                    marker="\nReserved rectangles in 96-DPI canvas coordinates: "
                    fixed_keys=("slide","slide_id","out","input_images","expected_backend","sample_generation_method")
                    same_art=(all(old_job.get(k)==job.get(k) for k in fixed_keys)
                              and old_job.get("prompt","").split(marker)[0]==job["prompt"].split(marker)[0])
                    accepted_sample=(sample_only is None
                                     and n in samples
                                     and state["approvals"].get("sample")
                                     and previous.get("status") in ("recorded","accepted"))
                    if not (same_art and accepted_sample):
                        raise ValueError(f"{sid}: recorded/dispatched job changed; use a new project or explicitly reset this slide")
                    previous["accepted_sample_layout"]={
                        "reserved_zones":zones,"reviewed_at":now_iso(),
                        "note":"Approved editable sample placement; original image prompt and provenance preserved"}
                entries.append(previous)
            else:
                write_json(root/job_ref,job)
                entries.append({
                    "slide_id":sid,"number":n,"job":job_ref,"out":job["out"],
                    "input_images":inputs,"requires_context_images":bool(inputs),
                    "status":"pending","dispatch":None,"result":None,"blocker":None,
                    **({"attempt_history":previous["attempt_history"]} if previous and previous.get("attempt_history") else {}),
                })
        # Repeated sample-only calls must not erase earlier sample provenance.
        if selection is not None:
            included={entry["number"] for entry in entries}
            entries.extend(entry for n,entry in old.items() if n not in included)
            entries.sort(key=lambda entry:entry["number"])
        jobs = {
            "version":1,"selected_backend":backend,
            "sample_generation_method":spec.get("background_generation_method",{}),
            "max_concurrent_slides":spec.get("max_concurrent_slides",3),
            "prepared_at":now_iso(),"slides":entries,"run_status":"prepared",
        }
        update_jobs_run_status(jobs)
        write_json(root/"slide_jobs.json",jobs)
    return jobs

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--spec",required=True);p.add_argument("--sample-only",type=int,nargs="+")
    p.add_argument("--checkpoint-only",type=int)
    a=p.parse_args();j=prepare(a.spec,a.sample_only,a.checkpoint_only)
    print(json.dumps({"jobs":len(j["slides"]),"status":j["run_status"]},ensure_ascii=False))
if __name__=="__main__":
    try:main()
    except (ValueError,FileNotFoundError) as exc:raise SystemExit(str(exc))
