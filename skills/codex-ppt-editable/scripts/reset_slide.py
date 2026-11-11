#!/usr/bin/env python3
"""Archive a rejected generated attempt before preparing its replacement. MIT."""
import argparse
import json
import shutil
from datetime import datetime,timezone
from pathlib import Path
from filelock import FileLock
from common import read_json,write_json,resolve
from intake import sample_numbers
from slide_run_state import locked_jobs,find_slide,update_jobs_run_status

def reset(project,number,reason):
    if not reason.strip():raise ValueError("A concrete repair reason is required")
    root=Path(project).resolve()
    with locked_jobs(root) as jobs:
        slide=find_slide(jobs,number)
        stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        folder=root/"generation_history"/slide["slide_id"]/stamp;folder.mkdir(parents=True)
        write_json(folder/"attempt.json",{"reason":reason,"slide":slide})
        for key,target in (("job","prompt.json"),("out","background.png")):
            path=resolve(root,slide.get(key,""))
            if path.is_file():shutil.copy2(path,folder/target)
        history=slide.setdefault("attempt_history",[]);history.append(str(folder.relative_to(root)))
        slide.update(status="pending",dispatch=None,result=None,blocker=None)
        update_jobs_run_status(jobs)
        with FileLock(str(root/".intake.lock")):
            intake=read_json(root/"intake.json")
            sample=intake.get("sample") or {}
            spec=read_json(root/"deck_spec.json")
            samples=sample.get("slides") or sample_numbers(spec)
            if slide["number"] in samples:
                intake["sample"]=None;intake["approvals"]["sample"]=False
                write_json(root/"intake.json",intake)
    return {"slide":number,"status":"pending","archived":str(folder)}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--project",required=True);p.add_argument("--slide",required=True);p.add_argument("--reason",required=True)
    a=p.parse_args();print(json.dumps(reset(a.project,a.slide,a.reason),ensure_ascii=False,indent=2))

if __name__=="__main__":
    try:main()
    except (ValueError,FileNotFoundError) as exc:raise SystemExit(str(exc))
