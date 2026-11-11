import copy
import unittest
from test_visual_workflow import slide
from diagram_style import engineering_contract
from visual_planning import validate_plans

class EngineeringStyleTests(unittest.TestCase):
    def setUp(self):
        self.spec={"schema_version":2,"visual_preference":"schematic","canvas":{"width":1280,"height":720},
                   "slides":[slide(1)]}
    def test_opt_in_contract_and_selective_emphasis(self):
        page=self.spec["slides"][0]
        self.assertIsNone(engineering_contract(self.spec,page))
        self.spec["diagram_style"]="engineering_wireframe";page["visual_plan"]["highlight_nodes"]=["b"]
        contract=engineering_contract(self.spec,page)
        self.assertEqual(contract["highlight_nodes"],["node_2"])
        self.assertEqual(contract["groups"],[])
        self.assertNotIn("PRIVATE_LABEL_NOT_FOR_BACKGROUND",str(contract))
        validate_plans(self.spec)
    def test_invalid_highlight_rejected(self):
        self.spec["diagram_style"]="engineering_wireframe"
        self.spec["slides"][0]["visual_plan"]["highlight_nodes"]=["unknown"]
        with self.assertRaisesRegex(ValueError,"highlight_nodes"):validate_plans(self.spec)
    def test_group_requires_real_members_and_containment(self):
        self.spec["diagram_style"]="engineering_wireframe";page=self.spec["slides"][0]
        page["visual_plan"]["groups"]=[{"kind":"parallel_stage","box":[60,200,1000,220],"members":["a","b"]}]
        c=engineering_contract(self.spec,page);self.assertEqual(c["groups"][0]["members"],["node_1","node_2"])
        page["visual_plan"]["groups"][0]["box"]=[60,200,300,220]
        with self.assertRaisesRegex(ValueError,"contain"):validate_plans(self.spec)
    def test_style_does_not_change_photos_or_tables(self):
        self.spec["diagram_style"]="engineering_wireframe";page=self.spec["slides"][0]
        for form in ("illustration","source_figure","table","data_chart"):
            page["visual_plan"]["form"]=form;self.assertIsNone(engineering_contract(self.spec,page))

if __name__=="__main__":unittest.main()
