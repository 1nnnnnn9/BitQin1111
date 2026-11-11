"""Behavioral and object tests; generated fixture images are NOT production art."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=ROOT/"skills"/"codex-ppt-editable"/"scripts"
sys.path.insert(0,str(SCRIPTS))
from common import write_json, check_assets
from intake import new_state, next_action, require_ready
from prepare_background_jobs import prepare
from assemble_editable_ppt import build
from validate_pptx import validate
from PIL import Image
from pptx import Presentation

def ready(sample=False):
    s=new_state()
    s["version"]=1  # Existing projects remain valid without inventing new answers.
    s["answers"]={"template":"none","style":"清爽专业风","materials":[],
                  "topic":"通用测试","audience":"课堂","slide_count":1,"backend":{"name":"built-in image tool","confirmed":True}}
    s["approvals"]={"outline":True,"sample":sample}
    return s

class IntakeTests(unittest.TestCase):
    def test_no_template_no_materials(self):
        s=new_state();self.assertEqual(next_action(s)["action"],"ask_template")
        s["answers"]["template"]="none";self.assertEqual(next_action(s)["action"],"choose_style")
        s["answers"]["style"]="清爽专业风";self.assertEqual(next_action(s)["action"],"ask_materials")
        s["answers"]["materials"]=[];self.assertEqual(next_action(s)["action"],"choose_visual_preference")
        s["answers"]["visual_preference"]="mixed";self.assertEqual(next_action(s)["action"],"clarify_brief")

    def test_template_with_materials_inspection_first(self):
        s=new_state();s["answers"].update(template="template.pptx",materials=["figure.png"])
        self.assertEqual(next_action(s)["action"],"inspect_template")
        s["answers"]["style"]={"name":"提取风格","inspected":True}
        self.assertEqual(next_action(s)["action"],"choose_visual_preference")

    def test_template_no_materials(self):
        s=new_state();s["answers"].update(template="template.pdf",style={"inspected":True})
        self.assertEqual(next_action(s)["action"],"ask_materials")
        s["answers"]["materials"]=[];self.assertEqual(next_action(s)["action"],"choose_visual_preference")

    def test_no_template_with_materials_no_repeat(self):
        s=ready();s["answers"]["materials"]=["figure.png"]
        self.assertEqual(next_action(s)["action"],"create_sample")
        s["sample"]={"pptx":"sample.pptx","preview":"sample.png"}
        self.assertEqual(next_action(s)["action"],"review_sample")
        s["approvals"]["sample"]=True
        self.assertEqual(next_action(s)["action"],"generate_full_deck")

    def test_gate_refuses_unanswered_and_unapproved(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):require_ready(temp)
            write_json(Path(temp)/"intake.json",ready())
            require_ready(temp)
            with self.assertRaises(ValueError):require_ready(temp,full=True)

class AssemblyTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        # This artificial bitmap is deliberately a UNIT TEST FIXTURE, not imagegen evidence.
        Image.new("RGB",(1280,720),"white").save(self.root/"background.png")
        Image.new("RGB",(400,200),"red").save(self.root/"source.png")
        self.spec={"title":"测试","backend":"built-in image tool","canvas":{"width":1280,"height":720},
            "style":{"name":"清爽专业风"},"assets":[{"id":"photo","path":"source.png","required":True}],
            "slides":[{"number":1,"scene_brief":"Right-side diagram","background":"background.png",
                "texts":[{"name":"正文","text":"第一行\n第二行","box":[40,40,500,120]},
                         {"name":"标签","text":"可编辑标签","box":[700,480,350,70]}],
                "images":[{"name":"原图","asset_id":"photo","box":[60,250,400,300],"crop":[.1,0,.1,0]}],
                "tables":[{"name":"表格","box":[650,150,500,200],"data":[["变量","数值"],["A","01.20"]]}],
                "notes":"测试讲稿","sources":["测试源"]}]}
        write_json(self.root/"deck_spec.json",self.spec)
        write_json(self.root/"intake.json",ready(True))
        # Explicit synthetic recorder fixture. No CLI provides fake provenance in normal usage.
        digest=hashlib.sha256((self.root/"background.png").read_bytes()).hexdigest()
        write_json(self.root/"slide_jobs.json",{"selected_backend":"built-in image tool","slides":[{
            "number":1,"status":"recorded","result":{"backend_used":"built-in image tool",
            "final_image":"background.png","final_image_sha256":digest,"sample_generation_method_matched":True}}]})
    def tearDown(self):self.tmp.cleanup()
    def test_native_objects_original_bytes_notes(self):
        build(self.root/"deck_spec.json",self.root/"test.pptx")
        self.assertTrue(validate(self.root/"deck_spec.json",self.root/"test.pptx")["ok"])
        prs=Presentation(self.root/"test.pptx")
        by={s.name:s for s in prs.slides[0].shapes}
        by["正文"].text="修改后的正文"
        by["标签"].text="修改后的标签"
        prs.save(self.root/"edited.pptx")
        reread=Presentation(self.root/"edited.pptx")
        texts={s.name:s.text for s in reread.slides[0].shapes if s.has_text_frame}
        self.assertEqual(texts["正文"],"修改后的正文");self.assertEqual(texts["标签"],"修改后的标签")
        self.spec["slides"][0]["texts"][0]["text"]="修改后的正文"
        self.spec["slides"][0]["texts"][1]["text"]="修改后的标签"
        write_json(self.root/"edited_spec.json",self.spec)
        self.assertTrue(validate(self.root/"edited_spec.json",self.root/"edited.pptx")["ok"])

    def test_sample_rejects_empty_native_shape_and_invalid_preview(self):
        from zipfile import ZipFile
        fake=self.root/"bad.pptx"
        with ZipFile(fake,"w") as z:
            z.writestr("ppt/slides/slide1.xml",'<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:sp/></p:sld>')
        (self.root/"bad.png").write_text("not an image")
        write_json(self.root/"intake.json",ready())
        cmd=[sys.executable,str(SCRIPTS/"intake.py"),"sample","--project",str(self.root),
             "--pptx",str(fake),"--preview",str(self.root/"bad.png")]
        result=subprocess.run(cmd,capture_output=True)
        self.assertNotEqual(result.returncode,0)
        # A valid text-bearing PPTX still requires a real decodable preview.
        build(self.root/"deck_spec.json",self.root/"sample.pptx",numbers=[1])
        cmd[cmd.index(str(fake))]=str(self.root/"sample.pptx")
        self.assertNotEqual(subprocess.run(cmd,capture_output=True).returncode,0)
        cmd[-1]=str(self.root/"background.png")
        result=subprocess.run(cmd,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_cover_crop_preserves_visible_aspect(self):
        self.spec["slides"][0]["images"][0]["fit"]="cover"
        write_json(self.root/"deck_spec.json",self.spec)
        build(self.root/"deck_spec.json",self.root/"cover.pptx")
        self.assertTrue(validate(self.root/"deck_spec.json",self.root/"cover.pptx")["ok"])

    def test_tampered_background_rejected(self):
        Image.new("RGB",(1280,720),"black").save(self.root/"background.png")
        with self.assertRaises(ValueError):build(self.root/"deck_spec.json",self.root/"test.pptx")

    def test_required_and_unused_assets(self):
        bad=copy.deepcopy(self.spec);bad["slides"][0]["images"]=[]
        with self.assertRaises(ValueError):check_assets(bad)
        bad["assets"][0]["required"]=False
        with self.assertRaises(ValueError):check_assets(bad)
        bad["assets"][0]["unused_reason"]="素材不适用于此主题"
        check_assets(bad)

    def test_background_prompt_excludes_native_strings(self):
        write_json(self.root/"intake.json",ready())
        self.spec["slides"][0]["texts"][0]["text"]="CONFIDENTIAL_TITLE_729"
        write_json(self.root/"deck_spec.json",self.spec)
        (self.root/"slide_jobs.json").unlink()
        prepare(self.root/"deck_spec.json",sample_only=1)
        prompt=json.loads((self.root/"prompts"/"slide_01.json").read_text(encoding="utf-8"))["prompt"]
        self.assertNotIn("CONFIDENTIAL_TITLE_729",prompt);self.assertIn("ABSOLUTELY NO TEXT",prompt)
        with self.assertRaises(ValueError):prepare(self.root/"deck_spec.json")

    def test_approved_sample_relayout_preserves_art_provenance(self):
        self.spec["sample_slide"]=1
        write_json(self.root/"deck_spec.json",self.spec)
        write_json(self.root/"intake.json",ready())
        (self.root/"slide_jobs.json").unlink()
        jobs=prepare(self.root/"deck_spec.json",sample_only=1)
        original_prompt=(self.root/"prompts/slide_01.json").read_bytes()
        jobs["slides"][0]["status"]="recorded"
        jobs["slides"][0]["result"]={"fixture":"synthetic unit-test provenance"}
        write_json(self.root/"slide_jobs.json",jobs)
        write_json(self.root/"intake.json",ready(True))
        self.spec["slides"][0]["texts"][1]["box"][0]+=20
        write_json(self.root/"deck_spec.json",self.spec)
        expanded=prepare(self.root/"deck_spec.json")
        self.assertEqual(expanded["slides"][0]["status"],"recorded")
        self.assertEqual(expanded["slides"][0]["result"],jobs["slides"][0]["result"])
        self.assertIn("accepted_sample_layout",expanded["slides"][0])
        self.assertEqual((self.root/"prompts/slide_01.json").read_bytes(),original_prompt)
        self.spec["slides"][0]["scene_brief"]="A different scientific diagram requiring new art"
        write_json(self.root/"deck_spec.json",self.spec)
        with self.assertRaises(ValueError):prepare(self.root/"deck_spec.json")

    def test_isolated_installation(self):
        isolated=self.root/"installed"/"codex-ppt-editable"
        shutil.copytree(SCRIPTS.parent,isolated,ignore=shutil.ignore_patterns("__pycache__"))
        env=os.environ.copy();env["PYTHONPATH"]=str(isolated/"scripts");env["PYTHONIOENCODING"]="utf-8"
        result=subprocess.run([sys.executable,str(isolated/"scripts"/"runtime.py"),"doctor"],
            cwd=self.root,env=env,capture_output=True,text=True,encoding="utf-8")
        self.assertEqual(result.returncode,0,result.stderr)
        result=subprocess.run([sys.executable,str(isolated/"scripts"/"intake.py"),"next","--project",str(self.root/"new")],
            cwd=self.root,env=env,capture_output=True,text=True,encoding="utf-8")
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)["action"],"ask_template")

if __name__=="__main__":unittest.main()
