# v2：保留完整视觉设计，再填可编辑文字

两页通用示例“雨水回用与运行管理”。使用随包 codex-ppt 的“教学课件风”完整视觉规范，由内置 image_gen 绘制背景、设施简图、图标、箭头和分区，只留空新增文字位置。标题、正文、标签、结论和备注由 python-pptx 添加。图形本身属于图片。

打开 [demonstration.pptx](demonstration.pptx) 查看正式结果，或查看 [整套预览](visual_review.montage.png)。[edited-demonstration.pptx](edited-demonstration.pptx) 与 [修改后预览](edited-preview.png) 展示实际修改正文和一个图示标签后的效果；正式文件保留原文。

这是维护者独立验证，未使用用户 PPT、个人资料或真实实验数据。监测屏幕中的曲线为概念图标，不是实测结果；示例不构成具体工程设计。维护者测试状态不能视为未来客户的样页批准。

## 新项目执行

复制 deck_spec.json 到新项目作为接口示例，并根据新内容重新设计。默认两页以上任务选择常规内容页和中后段复杂图解页；本例仅两页，因此两页均为样稿。示例的 resolved_node_boxes 是对已生成背景的观察，新图生成后应重新校准，不能照搬。

下面的 SKILL 指已安装的本技能目录；Python 需要 python-pptx、Pillow、filelock。新项目不需要原 codex-ppt 安装目录，也不需要本仓库路径。

1. `python SKILL/scripts/intake.py init --project PROJECT`。
2. 按 next 的结果确认模板、风格、素材、配图偏好和必要主题信息。已有答案直接记录，不重复问；用 `update --answers answers.json` 更新已知信息。
3. 编写大纲与逐页视觉规划，交付确认后运行 `approve --stage outline --artifact outline.md`；记录已确认的图片后端。
4. `python SKILL/scripts/prepare_background_jobs.py --spec PROJECT/deck_spec.json --sample-only 1 2`。
5. 按任务调用内置图片工具，每页通过 record_slide_dispatch.py 与 record_slide_result.py 记录实际生成来源。查看图形后校准原生标签位置；不要伪造来源或以代码绘图替代。
6. `python SKILL/scripts/assemble_editable_ppt.py --spec PROJECT/deck_spec.json --output PROJECT/sample.pptx --slides 1 2`。渲染并检查两页，向用户同时提供 PPTX 和各页预览。
7. `python SKILL/scripts/intake.py sample --project PROJECT --pptx sample.pptx --slides 1 2 --preview previews/slide-01.png previews/slide-02.png`。只有用户确认后才运行 `approve --stage sample`。本例两页的类型均已展示；更长的全稿还要按 intake next 的 approved_prefix 分段继续，首次新类型或明显版式变化先交代表页确认，不能把双样页批准当作全稿批准。
8. 组装全稿并渲染。`review_deck.py prepare` 生成缩略图和待填写记录；实际看图填写后，运行 `validate_pptx.py --final --visual-review visual_review.json`。完整参数见技能 references/quality-and-rendering.md。

已知答案示例（仅在会话已确认后记录）：

```json
{
  "template":"none",
  "style":"教学课件风",
  "materials":[],
  "visual_preference":"schematic",
  "topic":"雨水回用与运行管理",
  "audience":"课堂师生",
  "slide_count":2,
  "backend":{"name":"built-in image tool","confirmed":true}
}
```

配图偏好还可为 realistic 或 mixed；它与模板／配色分开记录。style.reference 读取内置风格，保留原 codex-ppt 的构图和图解表现。visual_plan 的 relationship_brief 允许自由设计；只有确需精确定位时才提供 nodes/relations，不要求每页采用方框网格。

## 验证证据

- generation-provenance.json 与 prompts/：真实图片工具、提示词、来源文件名及图片哈希。没有本机专有运行时或凭证。
- final-check.json 与 visual_review.json：原生对象、备注、图片比例及逐页观察；预览来自实际 PPTX 渲染。
- edited-object-check.json：修改正文及标签后重新打开 PPTX，验证文字仍为原生对象，图片和备注保留。
- 维护者在隔离复制的技能目录组装并验证本例，没有依赖原 codex-ppt 安装路径。新项目仍需自己的客户确认与生成状态。
