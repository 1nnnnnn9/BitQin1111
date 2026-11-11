# 原生可编辑组装接口

deck_spec.json 使用 UTF-8，相对路径相对于该文件；所有几何和 font_size 均为 96 DPI 像素。字号换算为 pt=px×0.75。先规划主图与关系，再协调原生文字留白。

```json
{
  "schema_version": 2,
  "title": "示例",
  "canvas": {"width": 1280, "height": 720},
  "font": "Microsoft YaHei",
  "style": {"name": "清爽专业风", "palette": ["#FFFFFF", "#163D3A"]},
  "backend": "built-in image tool",
  "visual_preference": "schematic",
  "sample_slides": [1],
  "assets": [
    {"id":"photo","path":"assets/photo.jpg","role":"原图","required":false,"unused_reason":"本页主题不涉及该内容"}
  ],
  "slides": [{
    "number":1,
    "scene_brief":"右侧简洁材料示意；左侧留白",
    "visual_plan":{"purpose":"overview","form":"illustration","explanation":"右侧材料层叠示意，说明材料形态","box":[760,180,460,400]},
    "background":"origin_image/slide_01.png",
    "texts":[
      {"name":"标题","text":"可编辑标题","box":[60,40,1100,70],"font_size":44,"bold":true,"color":"#163D3A"},
      {"name":"正文","text":"第一行\n第二行","box":[60,160,550,160],"font_size":28}
    ],
    "images":[],
    "tables":[],
    "notes":"可直接使用的讲稿",
    "sources":["来源链接或归属说明"]
  }]
}
```

## 对象

- texts：name、text、box必填。可选 font、font_size、bold、italic、color、align(left/center/right)、vertical_align(top/middle/bottom)、margin（默认0）。换行使用真正的 JSON 换行转义，不使用字面量反斜线+n。对象名在每页唯一。
- texts.role=diagram_label 用于生成图形内部的原生标签；普通标题／正文不要标为标签以绕过主图空间检查。
- images：asset_id引用assets中的id；或path直接指定。box必填。fit为contain（默认，保留整图比例）或cover（允许裁切）；crop为四个0–1比例[left,top,right,bottom]，表示先从原图四边裁去多少。不得裁掉关键证据。图片保留原始字节。
- tables：name、box、data（非空矩形二维字符串数组）；可选font_size、header_rows、column_widths（相对比例）、header_fill、header_color、cell_fill。数字字符串保持原值。native表格不是模型绘制的替代底图。
- assets：所有用户素材在此登记。unused_reason只用于未引用的可选素材；required=true未使用时拒绝最终组装。不要为凑数量使用无关素材。
- notes与sources：讲稿与来源写入对应页备注，source标注不自动进入可见页脚。
- source_asset_ids：本页实际采用的文字／文档资料的 assets.id 数组，记录正文或讲稿依据；不能为了通过检查而登记未采用的材料。图片和表格继续用其 asset_id 追踪。
- 可选background_generation_method：记录样页后端、工具、模式、提示词和实际输出；prepare脚本会携带到任务，原始资产不经过模型重画。
- style.reference：可选的内置风格名称，例如“教学课件风”。脚本读取随包风格文档的构图、配色、图解与视觉层次规范；style.name 恰好匹配内置名称时也自动读取。模板或自定义风格可在 style 中记录提取的完整视觉设计说明。除新增文字留白外，应保持原 codex-ppt 的视觉完整度。
- diagram_style：可选 engineering_wireframe；页面 visual_plan.diagram_style 可单独指定。该框图处理只影响相应图解；highlight_nodes 指定少量重点节点，groups 指定有真实含义的组框。字段与布局规则见 engineering-flowcharts.md；未指定时维持既有生成方式与来源。

背景文件必须存在并有真实的任务来源记录；测试夹具不作为生产图片来源。样页可单独导出；最终发布前用户应已确认样页。

## v2 视觉规划与双样页

新项目必填 schema_version=2、visual_preference（与 intake 一致）、sample_slides。两页以上任务选择两个不同的样页编号，按 slides 数组顺序排列；上面单页示例只有一个编号。旧版 sample_slide 标量保留兼容。

每页可记录 section 章节名称。visual_plan.visual_variant 记录同类型中的明显版式差异，例如 summary-table 与 dense-comparison；数据图可填写 chart_type。默认分段确认会识别真实表格／图片组合、流程拓扑及部分表格结构变化，执行代理仍须标记未被自动识别的视觉差异。新类型／变式的代表页批准后才继续，见 visual-checkpoints.md。

每页 visual_plan 必填 purpose、form、explanation。purpose 可为 overview、process、spatial、workstation、system、comparison、data、detail、conclusion、reference；form 可为 flowchart、block_layout、workstation、systems、diagram、data_chart、source_figure、illustration、table、text。

生成主图需要 box；flowchart、block_layout、workstation、systems 用 relationship_brief 说明实际结构即可；需要精确定位时提供至少两个 nodes 和一条 relations。节点不是必选的统一方框模板。source_figure 直接引用本页 images；table 需要本页原生表格。非明细／数据／参考页使用表格时提供 table_role 说明其辅助作用。

```json
"visual_plan": {
  "purpose":"process", "form":"flowchart",
  "explanation":"两阶段自左向右流转，连接代表物料流向",
  "box":[60,200,1160,400],
  "nodes":[
    {"id":"a","box":[100,300,300,120],"text_object":"阶段一标签"},
    {"id":"b","box":[800,300,300,120],"text_object":"阶段二标签"}
  ],
  "relations":[{"from":"a","to":"b","kind":"directed arrow"}]
}
```

text_object 对应 texts.name，标签框必须在节点框内部并标记 role=diagram_label。节点 ID 不会作为可见文字生成。relations 的 kind 描述有向箭头、双向连接、邻接或包含等实际关系。说明文字与标签文字分开：explanation 不应粘贴标题／标签。

生成图框体位置有偏差时，查看实际图片后可填写 visual_plan.resolved_node_boxes，例如 {"a":[110,310,300,120]}，并据此调整原生标签。原 nodes.box 保留生成目标，resolved_node_boxes 只记录实测布局，不进入模型提示词，也不能修复缺失／错误关系。

数据图额外提供 data 与 data_source，图形必须逐值核对。页面语义确实不适用默认图解形式时记录 exception_reason。视觉判断与语义归类仍由执行代理负责，脚本不能发现被故意错标的页面。具体选择依据见 visual-planning.md。
