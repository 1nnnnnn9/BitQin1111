"""Validate explanatory intent before allocating text-free generated art. MIT."""
from common import check_box

MODES={
    "schematic":"Prefer flat schematic drawing: orthographic or top-down views, crisp outlines, limited fills. Avoid photorealism, 3D perspective, material textures and ornamental shadows.",
    "realistic":"Prefer realistic or restrained three-dimensional illustrations where appearance is relevant. Still show the actual sequence, spatial arrangement or connections on explanatory pages; an equipment portrait is insufficient.",
    "mixed":"Choose appearance by the content: flat diagrams for sequence, space and relationships; realistic illustrations only when physical appearance helps explain the subject. Keep one coherent palette.",
}
REQUIRED_FORMS={
    "process":{"flowchart","source_figure"},
    "spatial":{"block_layout","source_figure"},
    "workstation":{"workstation","source_figure"},
    "system":{"systems","source_figure"},
}
FORMS={"flowchart","block_layout","workstation","systems","diagram","data_chart","source_figure","illustration","table","text"}
PURPOSES=set(REQUIRED_FORMS)|{"overview","comparison","data","detail","conclusion","reference"}
GENERATED=FORMS-{"source_figure","table","text"}

def intersection(a,b):
    return max(0,min(a[0]+a[2],b[0]+b[2])-max(a[0],b[0]))*max(0,min(a[1]+a[3],b[1]+b[3])-max(a[1],b[1]))

def inside(a,b):
    return a[0]>=b[0] and a[1]>=b[1] and a[0]+a[2]<=b[0]+b[2] and a[1]+a[3]<=b[1]+b[3]

def validate_plans(spec):
    """v1 stays readable; v2 requires a plan for each slide, not a picture quota."""
    if spec.get("schema_version",1)<2:return
    if spec.get("visual_preference") not in MODES:raise ValueError("Spec needs visual_preference")
    canvas=spec.get("canvas",{"width":1280,"height":720})
    for slide in spec["slides"]:
        tag=f"Slide {slide['number']}"
        plan=slide.get("visual_plan",{})
        purpose,form=plan.get("purpose"),plan.get("form")
        if purpose not in PURPOSES or form not in FORMS or not str(plan.get("explanation","")).strip():
            raise ValueError(f"{tag}: visual_plan needs purpose, form and explanation")
        if purpose in REQUIRED_FORMS and form not in REQUIRED_FORMS[purpose] and not plan.get("exception_reason"):
            raise ValueError(f"{tag}: {purpose} needs an explanatory diagram, not decorative art/table; explain any exception")
        if form=="table" and not slide.get("tables"):raise ValueError(f"{tag}: table plan has no native table")
        if form=="source_figure" and not slide.get("images"):raise ValueError(f"{tag}: source figure must be inserted directly")
        if slide.get("tables") and purpose not in {"detail","reference","data"} and not plan.get("table_role"):
            raise ValueError(f"{tag}: state the supporting role of tables")
        if form not in GENERATED:continue
        area=check_box(plan.get("box"),canvas,tag+"/visual_plan")
        for kind in ("texts","images","tables"):
            for obj in slide.get(kind,[]):
                box=check_box(obj["box"],canvas,tag+"/"+kind)
                overlap=intersection(area,box)
                if kind=="texts" and obj.get("role")=="diagram_label":continue
                if overlap>1:
                    raise ValueError(f"{tag}: {kind} overlaps the primary visual; move it or mark a true diagram label")
        nodes=plan.get("nodes",[]);ids=[n.get("id") for n in nodes]
        if any(not isinstance(n,str) or not n for n in ids) or len(set(ids))!=len(ids):
            raise ValueError(f"{tag}: node ids must be unique non-empty strings")
        texts={t["name"]:t for t in slide.get("texts",[])}
        actual_boxes=plan.get("resolved_node_boxes",{})
        if not isinstance(actual_boxes,dict) or set(actual_boxes)-set(ids):
            raise ValueError(f"{tag}: resolved_node_boxes must reference existing nodes")
        for node in nodes:
            box=check_box(node.get("box"),canvas,tag+"/node")
            if not inside(box,area):raise ValueError(f"{tag}: node lies outside visual area")
            if node["id"] in actual_boxes:
                box=check_box(actual_boxes[node["id"]],canvas,tag+"/resolved_node")
                if not inside(box,area):raise ValueError(f"{tag}: resolved node lies outside visual area")
            if node.get("text_object"):
                label=texts.get(node["text_object"])
                if not label or label.get("role")!="diagram_label" or not inside(label["box"],box):
                    raise ValueError(f"{tag}: node label must name an inset native diagram_label")
        relations=plan.get("relations",[])
        for edge in relations:
            if edge.get("from") not in ids or edge.get("to") not in ids or not edge.get("kind"):
                raise ValueError(f"{tag}: relation needs existing from/to nodes and kind")
        if form in {"flowchart","block_layout","workstation","systems"}:
            if nodes and (len(nodes)<2 or not relations):
                raise ValueError(f"{tag}: positioned diagram needs at least two nodes and a relationship")
            if not nodes and not str(plan.get("relationship_brief","")).strip():
                raise ValueError(f"{tag}: describe the actual relationship, either in nodes/relations or relationship_brief")
        if form=="data_chart" and (not plan.get("data") or not plan.get("data_source")):
            raise ValueError(f"{tag}: data chart needs explicit values and data_source")

def prompt_plan(plan):
    """Exclude native label strings/names. Opaque IDs specify geometry, never typography."""
    nodes=plan.get("nodes",[]);aliases={n["id"]:f"node_{i+1}" for i,n in enumerate(nodes)}
    result={k:plan[k] for k in ("purpose","form","explanation","relationship_brief","box","data","data_source") if k in plan}
    result["nodes"]=[{"id":aliases[n["id"]],"box":n["box"],"shape":n.get("shape","rectangle")} for n in nodes]
    result["relations"]=[{"from":aliases[e["from"]],"to":aliases[e["to"]],"kind":e["kind"]} for e in plan.get("relations",[])]
    return result
