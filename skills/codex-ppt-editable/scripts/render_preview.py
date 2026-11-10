#!/usr/bin/env python3
"""Portable optional preview: LibreOffice + Poppler. No bundled private runtime."""
from __future__ import annotations
import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

def render(pptx,output,soffice=None,pdftoppm=None):
    office=soffice or shutil.which("soffice")
    poppler=pdftoppm or shutil.which("pdftoppm")
    if not office or not poppler:
        raise RuntimeError("Preview unavailable: install LibreOffice + Poppler, provide executable paths, "
                           "or use the host presentation renderer / PowerPoint export. No visual QA was performed.")
    source=Path(pptx).resolve();out=Path(output).resolve();out.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="preview-",dir=out) as temp:
        temp=Path(temp)
        subprocess.run([office,"-env:UserInstallation="+(temp/"profile").as_uri(),"--headless",
            "--convert-to","pdf","--outdir",str(temp),str(source)],check=True,capture_output=True,text=True)
        pdf=temp/(source.stem+".pdf")
        if not pdf.exists():raise RuntimeError("LibreOffice produced no PDF")
        subprocess.run([poppler,"-png","-r","120",str(pdf),str(out/"slide")],check=True,capture_output=True,text=True)
    return sorted(str(p) for p in out.glob("slide-*.png"))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--pptx",required=True)
    p.add_argument("--output",required=True);p.add_argument("--soffice");p.add_argument("--pdftoppm")
    a=p.parse_args()
    try:print(json.dumps({"previews":render(a.pptx,a.output,a.soffice,a.pdftoppm)},ensure_ascii=False,indent=2))
    except RuntimeError as exc:raise SystemExit(str(exc))
if __name__=="__main__":main()
