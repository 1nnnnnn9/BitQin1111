"""Optional engineering flowchart treatment, independent from the deck palette. MIT."""
from common import check_box

def engineering_contract(spec,slide):
    plan=slide.get("visual_plan",{})
    selected=plan.get("diagram_style",spec.get("diagram_style"))
    if selected is None:return None
    if selected!="engineering_wireframe":raise ValueError("Unknown diagram_style: "+str(selected))
    if plan.get("form") not in {"flowchart","systems","diagram","block_layout","workstation"}:
        return None  # A flowchart choice must not flatten photos, charts or covers.
    nodes=plan.get("nodes",[]);ids=[n["id"] for n in nodes]
    aliases={key:f"node_{i+1}" for i,key in enumerate(ids)}
    highlights=plan.get("highlight_nodes",[])
    if not isinstance(highlights,list) or len(set(highlights))!=len(highlights) or set(highlights)-set(ids):
        raise ValueError(f"Slide {slide['number']}: highlight_nodes must reference distinct existing nodes")
    canvas=spec.get("canvas",{"width":1280,"height":720});groups=[]
    for i,group in enumerate(plan.get("groups",[])):
        members=group.get("members",[])
        if not group.get("kind") or len(members)<2 or len(set(members))!=len(members) or set(members)-set(ids):
            raise ValueError(f"Slide {slide['number']}: group needs a semantic kind and distinct existing members")
        box=check_box(group.get("box"),canvas,"diagram group")
        x,y,w,h=box
        for node in nodes:
            if node["id"] in members:
                nx,ny,nw,nh=node["box"]
                if nx<x or ny<y or nx+nw>x+w or ny+nh>y+h:
                    raise ValueError(f"Slide {slide['number']}: group must contain its member nodes")
        groups.append({"id":f"group_{i+1}","box":box,"kind":group["kind"],"members":[aliases[m] for m in members]})
    return {
        "name":"engineering_wireframe",
        "scope":"Diagram field only; retain the selected deck's title system and editable typography.",
        "reference_fidelity":"Follow the selected template/reference for background as well as linework. A plain-white engineering reference must not gain blue corner waves, ribbons, diagonal bands or ornamental page borders. Preserve any explicitly requested template treatment instead of inventing one.",
        "nodes":"Compact square-corner white or near-white process rectangles, thin neutral-gray outlines around 1 px on a 1280-wide slide. Adapt widths to label length and wrap needs; avoid uniformly oversized pale-cyan tiles. Blank interiors for native labels. No gradient, shadow, icon or ornamental border in this diagram field.",
        "connectors":"Crisp blue directional arrows around 1.5 px, consistent arrowheads. Use short orthogonal connectors, aligned lane centers and a shared merge trunk where useful; no crossing nodes or arbitrary detours.",
        "composition":"Group the process into a compact, balanced engineering figure with a clear reading order. Maintain generous external whitespace and modest, consistent gaps between nodes. Do not stretch a short chain merely to fill the page, and do not add a large surrounding frame to an ungrouped chain.",
        "emphasis":"Only the declared highlighted nodes receive a pale-blue fill and blue outline. Ordinary nodes remain neutral. Never color every stage as an equal highlight.",
        "highlight_nodes":[aliases[key] for key in highlights],
        "groups":groups,
        "group_rule":"Draw an enclosing frame only for an explicit semantic group below, such as parallel treatment lanes. Keep space for its native group heading. An empty group list means no enclosing process frame.",
        "label_guidance":"Native labels should be dark neutral, usually regular weight, centered with comfortable inset. Use bold lane/group headings selectively, not heavy bold text in every stage.",
    }
