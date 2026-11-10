#!/usr/bin/env python3
"""Prepare text-free image jobs; never render slide art in code."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from filelock import FileLock
from common import load_spec, check_box
from intake import require_ready
from slide_run_state import read_json, write_json, now_iso, update_jobs_run_status

def prepare(spec_path, sample_only=None):
    path, spec = load_spec(spec_path)
    root = path.parent
    state = require_ready(root, full=sample_only is None)
    backend = state["answers"]["backend"]["name"]
    if spec.get("backend", backend) != backend:
        raise ValueError("Spec backend differs from confirmed intake backend")
    canvas = spec.get("canvas", {"width":1280,"height":720})
    selected = [s for s in spec["slides"] if sample_only is None or s["number"] == sample_only]
    if not selected:
        raise ValueError("Sample slide does not exist")
    if sample_only is not None and len(selected) != 1:
        raise ValueError("Exactly one sample slide required")
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
            prompt = (
                "Create a professional slide BACKGROUND AND NON-TEXT ILLUSTRATION ONLY. "
                f"Landscape canvas aspect {canvas['width']}:{canvas['height']}. "
                "ABSOLUTELY NO TEXT: no titles, words, letters, numbers, labels, pseudo-writing, "
                "watermarks, signatures, legends or axes. Do not draw placeholder text or white cover-up boxes. "
                "The actual editable words and supplied original figures will be placed afterward in PowerPoint. "
                "Keep every reserved rectangle genuinely quiet and empty with a clean low-detail surface. "
                "Place all illustration outside those rectangles; do not invent experimental data. "
                "\nVisual style (ignore any legacy instruction to draw text): "
                + json.dumps(spec.get("style",{}),ensure_ascii=False)
                + "\nIllustration brief: " + slide.get("scene_brief","Minimal restrained visual background.")
                + "\nReserved rectangles in 96-DPI canvas coordinates: " + json.dumps(zones,ensure_ascii=False)
            )
            inputs = slide.get("style_reference_images", [])
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
            out = (root/job["out"]).resolve()
            out.relative_to(root)
            job_ref = f"prompts/{sid}.json"
            previous = old.get(n)
            if previous and previous.get("status") != "pending":
                old_job = read_json(root/job_ref)
                if old_job != job:
                    raise ValueError(f"{sid}: recorded/dispatched job changed; use a new project or explicitly reset this slide")
                entries.append(previous)
            else:
                write_json(root/job_ref,job)
                entries.append({
                    "slide_id":sid,"number":n,"job":job_ref,"out":job["out"],
                    "input_images":inputs,"requires_context_images":bool(inputs),
                    "status":"pending","dispatch":None,"result":None,"blocker":None,
                })
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
    p.add_argument("--spec",required=True);p.add_argument("--sample-only",type=int)
    a=p.parse_args();j=prepare(a.spec,a.sample_only)
    print(json.dumps({"jobs":len(j["slides"]),"status":j["run_status"]},ensure_ascii=False))
if __name__=="__main__":
    try:main()
    except (ValueError,FileNotFoundError) as exc:raise SystemExit(str(exc))
