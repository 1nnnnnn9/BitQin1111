"""Control-flow tests use synthetic images/PPTX fixtures, never production slide art."""
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
from test_visual_workflow import slide,state,SCRIPTS
from common import read_json,write_json
from intake import new_state,next_action
from prepare_background_jobs import prepare
from assemble_editable_ppt import build
from visual_checkpoints import frontier,visual_key,assert_selection,assert_final_approved,enabled,seed_samples
from reset_slide import reset

class VisualCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        pages=[slide(i) for i in range(1,7)]
        for i in (3,4):
            pages[i]["visual_plan"]={"purpose":"data","form":"table","explanation":"Tabular values as a new visual family"}
            pages[i]["texts"]=pages[i]["texts"][:1]
            pages[i]["tables"]=[{"name":"Data","box":[80,220,900,220],"data":[["Item","Value"],["A","1"]]}]
        pages[-1]["visual_plan"]["visual_variant"]="swimlane-with-controls"
        self.spec={"schema_version":2,"title":"Fixture","canvas":{"width":1280,"height":720},"style":{"name":"teaching"},
            "font":"Arial","backend":"built-in image tool","visual_preference":"schematic","sample_slides":[1,2],"slides":pages}
        self.save()
        s=state();s["answers"]["slide_count"]=6;s["visual_checkpoints"]={"enabled":True,"approvals":{},"drafts":{}}
        write_json(self.root/"intake.json",s)
        for i in range(1,7):
            Image.new("RGB",(1280,720),"white").save(self.root/f"bg{i}.png")
            Image.new("RGB",(1280,720),"white").save(self.root/f"preview{i}.png")
        prepare(self.root/"deck_spec.json",[1,2]);self.record([1,2])
        build(self.root/"deck_spec.json",self.root/"sample.pptx",[1,2])
        self.run_cli("intake.py","sample","--pptx","sample.pptx","--slides","1","2","--preview","preview1.png","preview2.png")
        self.run_cli("intake.py","approve","--stage","sample")
    def tearDown(self):self.tmp.cleanup()
    def save(self):write_json(self.root/"deck_spec.json",self.spec)
    def current(self):return read_json(self.root/"intake.json")
    def run_cli(self,script,*args,ok=True):
        env=os.environ.copy();env["PYTHONIOENCODING"]="utf-8"
        r=subprocess.run([sys.executable,str(SCRIPTS/script),*args,"--project",str(self.root)],capture_output=True,text=True,encoding="utf-8",env=env)
        if ok:self.assertEqual(r.returncode,0,r.stderr)
        else:self.assertNotEqual(r.returncode,0)
        return r
    def record(self,numbers):
        jobs=read_json(self.root/"slide_jobs.json")
        for j in jobs["slides"]:
            if j["number"] in numbers:
                path=self.root/f"bg{j['number']}.png"
                j.update(status="recorded",result={"backend_used":"built-in image tool","final_image":path.name,
                    "final_image_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"sample_generation_method_matched":True,
                    "fixture":"Synthetic unit-test evidence only"})
        write_json(self.root/"slide_jobs.json",jobs)
    def table_preview(self):
        prepare(self.root/"deck_spec.json",checkpoint_only=4);self.record([4])
        build(self.root/"deck_spec.json",self.root/"table.pptx",[4])
        self.run_cli("visual_checkpoints.py","register","--slide","4","--pptx","table.pptx","--preview","preview4.png")
    def test_first_table_stops_batch_and_is_not_globally_approved(self):
        self.assertTrue(enabled(new_state()))
        prefix,pending=frontier(self.spec,self.current());self.assertEqual(prefix,[1,2,3]);self.assertEqual(pending["slide"],4)
        prepared=prepare(self.root/"deck_spec.json")
        self.assertEqual([j["number"] for j in prepared["slides"]],[1,2,3])
        job=read_json(self.root/"prompts/slide_03.json")
        self.assertTrue(job["visual_checkpoint"]["anchor_images"])
        self.assertTrue(all(Path(p).is_file() for p in job["input_images"]))
        with self.assertRaises(ValueError):prepare(self.root/"deck_spec.json",checkpoint_only=5)
        with self.assertRaises(ValueError):build(self.root/"deck_spec.json",self.root/"too-early.pptx")
        with self.assertRaises(ValueError):assert_selection(self.spec,self.current(),[4,5])
        action=next_action(self.current(),self.root);self.assertEqual(action["action"],"create_visual_checkpoint")
        self.assertEqual(action["slide"],4)
    def test_table_approval_continues_similar_tables_then_stops_variant(self):
        self.table_preview()
        self.assertEqual(next_action(self.current(),self.root)["action"],"review_visual_checkpoint")
        self.run_cli("visual_checkpoints.py","approve","--slide","4")
        prefix,pending=frontier(self.spec,self.current());self.assertEqual(prefix,[1,2,3,4,5]);self.assertEqual(pending["slide"],6)
        # Same approved diagram family does not authorize a markedly different layout variant.
        with self.assertRaises(ValueError):assert_selection(self.spec,self.current(),None)
    def test_reject_offers_choices_and_choice_is_not_approval(self):
        self.table_preview()
        options=[{"id":"A","label":"More whitespace","description":"Reduce content density and widen columns"},
                 {"id":"B","label":"Split the table","description":"Separate summary values and detailed rows"}]
        write_json(self.root/"options.json",options)
        self.run_cli("visual_checkpoints.py","reject","--slide","4","--reason","The table is too dense","--options","options.json")
        self.assertEqual(next_action(self.current(),self.root)["action"],"choose_visual_revision")
        self.run_cli("visual_checkpoints.py","choose","--slide","4","--option","B")
        self.run_cli("visual_checkpoints.py","approve","--slide","4",ok=False)
        self.run_cli("visual_checkpoints.py","register","--slide","4","--pptx","table.pptx","--preview","preview4.png",ok=False)
        self.spec["slides"][3]["texts"][0]["text"]="Revised table summary";self.save()
        build(self.root/"deck_spec.json",self.root/"revised.pptx",[4])
        Image.new("RGB",(1280,720),"#F8FAFC").save(self.root/"revised-preview.png")
        self.run_cli("visual_checkpoints.py","register","--slide","4","--pptx","revised.pptx","--preview","revised-preview.png")
        self.assertEqual(next_action(self.current(),self.root)["action"],"review_visual_checkpoint")
        self.run_cli("visual_checkpoints.py","approve","--slide","4")
        self.assertEqual(frontier(self.spec,self.current())[1]["slide"],6)
    def test_invalid_options_and_stale_artifacts_do_not_pass(self):
        self.table_preview();write_json(self.root/"options.json",[{"id":"A","label":"Only one","description":"Insufficient alternatives"}])
        self.run_cli("visual_checkpoints.py","reject","--slide","4","--reason","Dense","--options","options.json",ok=False)
        draft=next(iter(self.current()["visual_checkpoints"]["drafts"].values()))
        Path(draft["preview"]).write_bytes(b"tampered")
        self.run_cli("visual_checkpoints.py","approve","--slide","4",ok=False)
    def test_composite_table_and_flowchart_and_branching_are_new_keys(self):
        linear=slide(1);branched=slide(2);branched["visual_plan"]["relations"].append({"from":"a","to":"a","kind":"feedback"})
        self.assertNotEqual(visual_key(linear),visual_key(branched))
        mixed=copy.deepcopy(linear);mixed["tables"]=[{"data":[["x"]]}]
        self.assertNotEqual(visual_key(linear),visual_key(mixed))
    def test_legacy_enable_preserves_only_explicit_sample_approvals(self):
        s=self.current();s.pop("visual_checkpoints");write_json(self.root/"intake.json",s)
        self.run_cli("visual_checkpoints.py","enable")
        self.assertEqual(frontier(self.spec,self.current())[1]["slide"],4)
    def test_recorded_checkpoint_prompts_and_anchors_stay_immutable(self):
        self.table_preview();self.run_cli("visual_checkpoints.py","approve","--slide","4")
        before=(self.root/"prompts/slide_04.json").read_bytes()
        jobs=prepare(self.root/"deck_spec.json")
        self.assertEqual(before,(self.root/"prompts/slide_04.json").read_bytes())
        self.assertEqual(next(j for j in jobs["slides"] if j["number"]==4)["status"],"recorded")

    def test_wide_table_is_not_covered_by_small_summary_approval(self):
        self.table_preview();self.run_cli("visual_checkpoints.py","approve","--slide","4")
        self.spec["slides"][4]["tables"][0]["data"]=[[str(c) for c in range(6)] for _ in range(6)];self.save()
        self.assertNotEqual(visual_key(self.spec["slides"][3]),visual_key(self.spec["slides"][4]))
        self.assertEqual(frontier(self.spec,self.current())[1]["slide"],5)

    def test_reset_representative_revokes_its_family_approval(self):
        self.table_preview();self.run_cli("visual_checkpoints.py","approve","--slide","4")
        reset(self.root,4,"Rework this representative")
        self.assertEqual(frontier(self.spec,self.current())[1]["slide"],4)
        with self.assertRaises(ValueError):assert_selection(self.spec,self.current(),[5])

    def test_old_prepared_jobs_cannot_bypass_dispatch_or_result_gate(self):
        s=self.current();s["visual_checkpoints"]["enabled"]=False;write_json(self.root/"intake.json",s)
        prepare(self.root/"deck_spec.json")  # Fixture emulates old v2 whole-deck preparation.
        s["visual_checkpoints"]["enabled"]=True;write_json(self.root/"intake.json",s)
        prepare(self.root/"deck_spec.json")
        env=os.environ.copy();env["PYTHONIOENCODING"]="utf-8"
        command=[sys.executable,str(SCRIPTS/"record_slide_dispatch.py"),str(self.root),"--slide","5","--agent-id","synthetic-test"]
        r=subprocess.run(command,capture_output=True,text=True,encoding="utf-8",env=env)
        self.assertNotEqual(r.returncode,0);self.assertIn("visual checkpoint",r.stderr)
        r=subprocess.run([sys.executable,str(SCRIPTS/"slide_job_status.py"),str(self.root),"--json"],capture_output=True,text=True,encoding="utf-8",env=env)
        self.assertEqual(r.returncode,0,r.stderr);self.assertNotIn("slide_05",json.loads(r.stdout)["dispatchable_slides"])
        jobs=read_json(self.root/"slide_jobs.json");future=next(j for j in jobs["slides"] if j["number"]==5)
        future.update(status="dispatched",dispatch={"agent_id":"synthetic-test"});write_json(self.root/"slide_jobs.json",jobs)
        r=subprocess.run([sys.executable,str(SCRIPTS/"record_slide_result.py"),str(self.root),"--slide","5","--agent-id","synthetic-test",
            "--backend-used","built-in image tool","--selected-source",str(self.root/"bg5.png"),"--qa-note","Synthetic negative gate test"],capture_output=True,text=True,encoding="utf-8",env=env)
        self.assertNotEqual(r.returncode,0);self.assertIn("visual checkpoint",r.stderr)
        self.assertIsNone(next(j for j in read_json(self.root/"slide_jobs.json")["slides"] if j["number"]==5)["result"])

    def test_all_reviewed_families_allow_full_assembly(self):
        self.table_preview();self.run_cli("visual_checkpoints.py","approve","--slide","4")
        prepare(self.root/"deck_spec.json",checkpoint_only=6);self.record([6]);build(self.root/"deck_spec.json",self.root/"variant.pptx",[6])
        self.run_cli("visual_checkpoints.py","register","--slide","6","--pptx","variant.pptx","--preview","preview6.png")
        self.run_cli("visual_checkpoints.py","approve","--slide","6")
        self.assertIsNone(frontier(self.spec,self.current())[1]);assert_final_approved(self.spec,self.current())
        prepare(self.root/"deck_spec.json");self.record([1,2,3,4,5,6]);build(self.root/"deck_spec.json",self.root/"full.pptx")

    def test_initial_pending_and_changed_theme_block_final_completion(self):
        s=self.current();s["approvals"]["sample"]=False
        with self.assertRaisesRegex(ValueError,"Initial"):assert_final_approved(self.spec,s)
        self.spec["style"]["palette"]=["#000000","#FFFFFF"];self.save()
        self.assertEqual(frontier(self.spec,self.current())[1]["slide"],1)


if __name__=="__main__":unittest.main()
