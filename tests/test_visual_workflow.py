"""V2 behavioral checks. All generated test bitmaps are synthetic fixtures, not art."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from PIL import Image
from pptx import Presentation

SCRIPTS=Path(__file__).resolve().parents[1]/"skills"/"codex-ppt-editable"/"scripts"
sys.path.insert(0,str(SCRIPTS))
from common import read_json,write_json,check_assets
from intake import new_state,next_action,require_ready,sample_numbers
from visual_planning import validate_plans
from prepare_background_jobs import prepare
from assemble_editable_ppt import build
from review_deck import prepare_review,check_review,CHECKS
from reset_slide import reset

def state(approved=False):
    s=new_state();s["answers"]={"template":"none","style":"teaching","materials":[],"visual_preference":"schematic",
        "topic":"test","audience":"class","slide_count":3,"backend":{"name":"built-in image tool","confirmed":True}}
    s["approvals"]={"outline":True,"sample":approved}
    if approved:s["sample"]={"slides":[1,3],"pptx":"sample.pptx","previews":["1.png","3.png"]}
    return s

def slide(n,purpose="process",form="flowchart"):
    return {"number":n,"background":f"bg{n}.png","scene_brief":"Draw the planned explanatory diagram.",
        "texts":[{"name":"Title","text":f"Native title {n}","box":[60,40,1100,70]},
                 {"name":"Left label","text":"PRIVATE_LABEL_NOT_FOR_BACKGROUND","role":"diagram_label","box":[100,290,180,40]},
                 {"name":"Right label","text":"Next stage","role":"diagram_label","box":[700,290,180,40]}],
        "visual_plan":{"purpose":purpose,"form":form,"explanation":"A directed transition between two stages.","box":[60,180,1100,400],
            "nodes":[{"id":"a","box":[80,250,240,120],"text_object":"Left label"},
                     {"id":"b","box":[680,250,240,120],"text_object":"Right label"}],
            "relations":[{"from":"a","to":"b","kind":"directed arrow"}]},"notes":"Speaker notes"}

class VisualWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.spec={"schema_version":2,"title":"Fixture","backend":"built-in image tool","visual_preference":"schematic",
            "canvas":{"width":1280,"height":720},"sample_slides":[1,3],"slides":[slide(1),slide(2),slide(3,"system","systems")]}
        self.save();write_json(self.root/"intake.json",state())
        for n in range(1,4):Image.new("RGB",(1280,720),"white").save(self.root/f"bg{n}.png")
    def tearDown(self):self.tmp.cleanup()
    def save(self):write_json(self.root/"deck_spec.json",self.spec)
    def cli(self,*args):
        env=os.environ.copy();env["PYTHONIOENCODING"]="utf-8"
        return subprocess.run([sys.executable,str(SCRIPTS/"intake.py"),*args,"--project",str(self.root)],env=env,capture_output=True,text=True,encoding="utf-8")
    def record_fixture(self,numbers=(1,2,3)):
        # Never used by real callers; tests alone create synthetic recorder evidence.
        jobs={"selected_backend":"built-in image tool","slides":[]}
        for n in numbers:
            jobs["slides"].append({"number":n,"status":"recorded","result":{"backend_used":"built-in image tool",
                "final_image":f"bg{n}.png","final_image_sha256":hashlib.sha256((self.root/f"bg{n}.png").read_bytes()).hexdigest(),
                "sample_generation_method_matched":True}})
        write_json(self.root/"slide_jobs.json",jobs)

    def test_intake_four_scenarios_and_known_answers(self):
        for template in ("none","template.pptx"):
            for materials in ([],["original.png"]):
                with self.subTest(template=template,materials=materials):
                    s=new_state();s["answers"]={"template":template,"materials":materials}
                    self.assertEqual(next_action(s)["action"],"choose_style" if template=="none" else "inspect_template")
                    s["answers"]["style"]={"inspected":True}
                    self.assertEqual(next_action(s)["action"],"choose_visual_preference")
                    s["answers"]["visual_preference"]="mixed"
                    self.assertEqual(next_action(s)["action"],"clarify_brief")
        self.assertEqual(next_action(state())["count"],2)
        s=state();s["answers"].pop("visual_preference");write_json(self.root/"intake.json",s)
        with self.assertRaisesRegex(ValueError,"Visual preference"):require_ready(self.root)

    def test_invalid_preference_rejected_without_state_change(self):
        original=(self.root/"intake.json").read_bytes();write_json(self.root/"answers.json",{"visual_preference":"unknown"})
        self.assertNotEqual(self.cli("update","--answers",str(self.root/"answers.json")).returncode,0)
        self.assertEqual(original,(self.root/"intake.json").read_bytes())

    def test_preference_change_invalidates_sample(self):
        write_json(self.root/"intake.json",state(True));write_json(self.root/"answers.json",{"visual_preference":"mixed"})
        self.assertEqual(self.cli("update","--answers",str(self.root/"answers.json")).returncode,0)
        changed=read_json(self.root/"intake.json");self.assertFalse(changed["approvals"]["sample"]);self.assertIsNone(changed["sample"])

    def test_semantic_diagram_pages_reject_decoration_or_tables(self):
        for purpose in ("process","spatial","workstation","system"):
            for form in ("illustration","table"):
                with self.subTest(purpose=purpose,form=form):
                    s=copy.deepcopy(self.spec);s["slides"][0]["visual_plan"].update(purpose=purpose,form=form)
                    with self.assertRaisesRegex(ValueError,"explanatory diagram"):validate_plans(s)

    def test_table_and_reference_pages_do_not_require_diagram_quota(self):
        s=copy.deepcopy(self.spec);p=s["slides"][0];p["visual_plan"]={"purpose":"detail","form":"table","explanation":"Detailed source values"}
        p["tables"]=[{"name":"Values","box":[60,180,1100,400],"data":[["A","2"]]}];validate_plans(s)

    def test_relationship_and_space_conflicts_rejected(self):
        self.spec["slides"][0]["visual_plan"]["relations"][0]["to"]="missing"
        with self.assertRaisesRegex(ValueError,"relation"):validate_plans(self.spec)
        self.spec["slides"][0]=slide(1)
        self.spec["slides"][0]["tables"]=[{"box":[60,180,1100,400]}]
        self.spec["slides"][0]["visual_plan"]["table_role"]="supporting details"
        with self.assertRaisesRegex(ValueError,"overlaps"):validate_plans(self.spec)

    def test_modes_change_real_jobs_without_native_text_leakage(self):
        prompts=[]
        for mode in ("schematic","realistic","mixed"):
            self.spec["visual_preference"]=mode;self.save()
            s=state();s["answers"]["visual_preference"]=mode;write_json(self.root/"intake.json",s)
            prepare(self.root/"deck_spec.json",[1,3]);job=read_json(self.root/"prompts/slide_01.json")
            prompts.append(job["prompt"])
            self.assertNotIn("PRIVATE_LABEL_NOT_FOR_BACKGROUND",job["prompt"])
            self.assertEqual(job["background_contract"]["text_free"],True)
            self.assertIn('"from": "node_1", "to": "node_2"',job["prompt"])
        self.assertEqual(len(set(prompts)),3)

    def test_sample_calls_preserve_both_jobs_and_block_other_pages(self):
        prepare(self.root/"deck_spec.json",1);jobs=prepare(self.root/"deck_spec.json",3)
        self.assertEqual([s["number"] for s in jobs["slides"]],[1,3])
        with self.assertRaises(ValueError):prepare(self.root/"deck_spec.json",2)
        with self.assertRaises(ValueError):prepare(self.root/"deck_spec.json")

    def test_dual_native_sample_registration_and_gate(self):
        self.record_fixture();build(self.root/"deck_spec.json",self.root/"sample.pptx",numbers=[1,3])
        with self.assertRaises(ValueError):build(self.root/"deck_spec.json",self.root/"early.pptx",numbers=[2])
        with self.assertRaises(ValueError):build(self.root/"deck_spec.json",self.root/"early.pptx")
        args=("sample","--pptx",str(self.root/"sample.pptx"),"--slides","1","3","--preview",str(self.root/"bg1.png"))
        self.assertNotEqual(self.cli(*args).returncode,0)
        self.assertEqual(self.cli(*args,str(self.root/"bg3.png")).returncode,0)
        self.assertEqual(next_action(read_json(self.root/"intake.json"))["action"],"review_sample")
        self.assertEqual(self.cli("approve","--stage","sample").returncode,0)
        build(self.root/"deck_spec.json",self.root/"full.pptx")

    def test_single_slide_task_and_legacy_sample_contract(self):
        self.spec["slides"]=self.spec["slides"][:1];self.spec["sample_slides"]=[1];self.assertEqual(sample_numbers(self.spec),[1])
        self.assertEqual(sample_numbers({"sample_slide":3,"slides":[slide(1),slide(3)]}),[3])
        self.spec["slides"]=[slide(1),slide(3)];self.spec["sample_slides"]=[3,1]
        with self.assertRaisesRegex(ValueError,"order"):sample_numbers(self.spec)

    def test_document_material_usage_and_unknown_source_ids(self):
        self.spec["assets"]=[{"id":"notes","path":"notes.txt","required":True}]
        with self.assertRaisesRegex(ValueError,"unused"):check_assets(self.spec)
        self.spec["slides"][0]["source_asset_ids"]=["notes"];check_assets(self.spec)
        self.spec["slides"][0]["source_asset_ids"]=["missing"]
        with self.assertRaisesRegex(ValueError,"Unknown"):check_assets(self.spec)

    def test_both_accepted_sample_layouts_preserve_prompts(self):
        jobs=prepare(self.root/"deck_spec.json",[1,3]);before={n:(self.root/f"prompts/slide_{n:02d}.json").read_bytes() for n in (1,3)}
        for entry in jobs["slides"]:entry["status"]="recorded";entry["result"]={"test_fixture":True}
        write_json(self.root/"slide_jobs.json",jobs);write_json(self.root/"intake.json",state(True))
        for n in (1,3):self.spec["slides"][n-1]["texts"][0]["box"][0]+=10
        self.save();expanded=prepare(self.root/"deck_spec.json")
        for entry in expanded["slides"]:
            if entry["number"] in before:
                self.assertIn("accepted_sample_layout",entry)
                self.assertEqual((self.root/f"prompts/slide_{entry['number']:02d}.json").read_bytes(),before[entry["number"]])

    def test_review_requires_real_observations_and_detects_stale_artifacts(self):
        write_json(self.root/"intake.json",state(True));self.record_fixture();build(self.root/"deck_spec.json",self.root/"full.pptx")
        q=self.root/"review.json";previews=[self.root/f"bg{n}.png" for n in (1,2,3)]
        review=prepare_review(self.root/"deck_spec.json",self.root/"full.pptx",previews,q)
        self.assertFalse(check_review(self.root/"deck_spec.json",self.root/"full.pptx",q)["ok"])
        review["whole_deck"]={"visual_balance":True,"later_section_quality":True,"observation":"Synthetic unit-test review only"}
        for row in review["slides"]:row["checks"]=dict.fromkeys(CHECKS,True);row["observation"]="Test fixture, not real visual approval"
        write_json(q,review);self.assertTrue(check_review(self.root/"deck_spec.json",self.root/"full.pptx",q)["ok"])
        spec_file=self.root/"deck_spec.json"
        spec_file.write_bytes(spec_file.read_bytes().replace(b"\r\n",b"\n"))
        self.assertTrue(check_review(spec_file,self.root/"full.pptx",q)["ok"])
        Image.new("RGB",(1280,720),"black").save(previews[-1])
        self.assertFalse(check_review(self.root/"deck_spec.json",self.root/"full.pptx",q)["ok"])

    def test_duplicate_review_paths_rejected(self):
        with self.assertRaisesRegex(ValueError,"own preview"):
            prepare_review(self.root/"deck_spec.json",self.root/"unused.pptx",[self.root/"bg1.png"]*3,self.root/"review.json")

    def test_resolved_node_geometry_keeps_generation_plan(self):
        from visual_planning import prompt_plan
        plan=self.spec["slides"][0]["visual_plan"];original=prompt_plan(plan)
        plan["resolved_node_boxes"]={"a":[80,260,240,120]}
        validate_plans(self.spec);self.assertEqual(prompt_plan(plan),original)
        plan["resolved_node_boxes"]["missing"]=[80,260,240,120]
        with self.assertRaises(ValueError):validate_plans(self.spec)

    def test_complete_upstream_style_carried_and_free_composition_supported(self):
        from style_contract import visual_style
        style=visual_style({"name":"教学课件风"})
        self.assertTrue(style["codex_ppt_visual_guide"]["layout_patterns"])
        self.assertTrue(style["codex_ppt_visual_guide"]["image_treatment"])
        self.assertNotIn("layout_blueprints",style["codex_ppt_visual_guide"])
        plan=self.spec["slides"][0]["visual_plan"];plan.pop("nodes");plan.pop("relations")
        plan["relationship_brief"]="Two processing stages connect left to right; retain a meaningful illustration for each."
        validate_plans(self.spec)
        plan.pop("relationship_brief")
        with self.assertRaisesRegex(ValueError,"actual relationship"):validate_plans(self.spec)

    def test_reset_archives_attempt_and_invalidates_sample(self):
        jobs=prepare(self.root/"deck_spec.json",[1,3]);jobs["slides"][0]["status"]="recorded";jobs["slides"][0]["result"]={"test_fixture":True}
        write_json(self.root/"slide_jobs.json",jobs);write_json(self.root/"intake.json",state(True))
        result=reset(self.root,1,"Replace incorrect relationship")
        archived=read_json(Path(result["archived"])/"attempt.json")
        self.assertEqual(archived["slide"]["result"],{"test_fixture":True})
        self.assertFalse(read_json(self.root/"intake.json")["approvals"]["sample"])
        jobs=prepare(self.root/"deck_spec.json",[1,3]);self.assertTrue(jobs["slides"][0]["attempt_history"])

    def test_reset_legacy_default_sample_invalidates_registration(self):
        legacy=copy.deepcopy(self.spec);legacy.pop("schema_version");legacy.pop("sample_slides")
        write_json(self.root/"deck_spec.json",legacy)
        s=state(True);s["version"]=1;s["sample"]={"pptx":"old.pptx","preview":"old.png"}
        write_json(self.root/"intake.json",s)
        write_json(self.root/"slide_jobs.json",{"slides":[{"number":1,"slide_id":"slide_01","status":"recorded","out":"bg1.png","result":{"test_fixture":True}}]})
        reset(self.root,1,"Fix the default legacy sample")
        s=read_json(self.root/"intake.json")
        self.assertIsNone(s["sample"]);self.assertFalse(s["approvals"]["sample"])

if __name__=="__main__":unittest.main()
