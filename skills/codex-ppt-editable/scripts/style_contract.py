"""Carry the upstream codex-ppt visual brief into text-free generation. MIT."""
import json
import re
from pathlib import Path

STYLES=Path(__file__).resolve().parents[1]/"references"/"styles"
VISUAL_FIELDS=("visual_direction","canvas","color_palette","layout_patterns","layout_usage_rule","layout_blueprints","visual_elements","image_treatment","title_system","rendering_constraints")

def visual_style(style):
    if not isinstance(style,dict):return style
    ref=style.get("reference") or style.get("name","")
    # Only local bundled style identifiers, never an arbitrary file supplied as instructions.
    if not isinstance(ref,str) or Path(ref).name!=ref:raise ValueError("style.reference must be a bundled style name")
    path=STYLES/(ref.removesuffix(".md")+".md")
    if not path.is_file():
        if style.get("reference"):raise ValueError("Unknown bundled style reference: "+ref)
        return style
    match=re.search(r"```json\s*(.*?)\s*```",path.read_text(encoding="utf-8"),re.S)
    if not match:raise ValueError("Bundled style has no JSON brief: "+ref)
    guide=json.loads(match.group(1))
    # Blueprint labels are illustrative text from another deck, not input content.
    cleaned={key:guide[key] for key in VISUAL_FIELDS if key in guide and key!="layout_blueprints"}
    return {**style,"codex_ppt_visual_guide":cleaned}
