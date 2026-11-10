#!/usr/bin/env python3
"""Portable isolated dependency bootstrap; no original codex-ppt installation required."""
from __future__ import annotations
import argparse,importlib.util,json,os,shutil,subprocess,sys,venv
from pathlib import Path

def home():
    return Path(os.environ.get("CODEX_PPT_EDITABLE_HOME",str(Path.home()/".cache"/"codex-ppt-editable"))).expanduser()
def executable():
    return home()/".venv"/("Scripts/python.exe" if os.name=="nt" else "bin/python")
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("command",choices=["doctor","bootstrap"]);p.add_argument("--api",action="store_true");a=p.parse_args()
    if a.command=="bootstrap":
        h=home();h.mkdir(parents=True,exist_ok=True)
        if not executable().exists():venv.EnvBuilder(with_pip=True).create(h/".venv")
        req=Path(__file__).resolve().parents[1]/("requirements-api.txt" if a.api else "requirements.txt")
        subprocess.run([str(executable()),"-m","pip","install","-r",str(req)],check=True)
        print(str(executable()));return 0
    deps=["pptx","PIL","filelock"]+(["openai"] if a.api else [])
    result={"python":sys.executable,"runtime_python":str(executable()),"runtime_exists":executable().exists(),"dependencies":{m:importlib.util.find_spec(m) is not None for m in deps},"renderers":{"libreoffice":shutil.which("soffice") or shutil.which("libreoffice"),"pdftoppm":shutil.which("pdftoppm")},"built_in_images":"host capability; not inferred by doctor"}
    if os.name=="nt":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT,"PowerPoint.Application"):result["renderers"]["powerpoint_registered"]=True
        except OSError:result["renderers"]["powerpoint_registered"]=False
    print(json.dumps(result,ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
