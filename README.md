# BitQin1111 · Codex PPT Editable

基于 [ningzimu/codex-ppt-skill](https://github.com/ningzimu/codex-ppt-skill) 的独立增强技能。
**先问模板 → 无模板时选风格 → 再问素材 → 单独选配图偏好 → 双样页确认 → 新视觉部分逐段确认 → 全稿检查。**

这不是整页截图式 PPT，也不是用代码绘制底图。新绘制的背景、示意图、装饰图标使用 codex-ppt 的图片生成流程；Python 负责文字、用户原图、表格、备注的排版和检查。生成图片可以合并非文字视觉内容，所有新增文字保留为 PowerPoint 对象。

**核心目标：保留 codex-ppt 的完整页面视觉效果，仅把新增文字位置留空，最后填入可编辑文字。** 原风格的构图、图解、层次与配图继续由图片模型完成，不把“可编辑”做成统一方框或大表格母版。

![可编辑示例预览](examples/visual-planning/previews/slide-01.png)

[查看新版示例](examples/visual-planning/demonstration.pptx) · [制作与验证说明](examples/visual-planning/README.md) · [旧版兼容示例](examples/minimal/README.md)

## 安装

只安装本仓库内的 `skills/codex-ppt-editable`，**不需要安装原 codex-ppt**。

在 Codex 中使用内置 skill-installer，提供：
- 仓库：`1nnnnnn9/BitQin1111`
- 路径：`skills/codex-ppt-editable`

也可以下载仓库，把该目录放到自己的 skills 目录，保持目录名为 `codex-ppt-editable`。使用项目级技能时按宿主支持的项目 skills 路径安装即可。不要把本 README 所在的仓库根目录误当作技能目录。

首次使用：
> 使用 $codex-ppt-editable 为我制作一份可编辑 PPT。

正常自动发现保持启用；也可通过上述名称显式调用。

## 使用流程

1. 首先确认有无 PPT 模板。已有附件或答案时直接采用，不反复询问。
2. 有模板：先查看代表性页面，提取配色、字体、视觉语言；默认只参考风格，重新组织版式。没有模板：从内置 12 种 codex-ppt 风格中推荐 2–3 种供选择。
3. 接着确认素材，包括图片、图标、图表、表格数据和文字。建立使用清单，尽可能采用相关素材，未用素材说明原因。
4. 单独选择配图偏好：简略示意图为主、写实／三维图为主，或按内容混合。已有明确答案不再问；模板和配色不代替此项选择。
5. 确认大纲与逐页视觉规划。流程、空间、工位、系统关系优先安排适合的图解，详细数据与附录保留表格，不硬设图解页比例。
6. 先交付常规内容页＋中后段复杂图解页及预览。批准只覆盖这两页展示过的视觉类型／版式；单页任务仅一页。
7. 后续遇到表格、流程图、图表等新视觉部分，或明显不同的版式，先交付一张完整可编辑代表页等待确认。不满意时给2–3个具体方向，选择后修订并再次展示；满意才继续同类后续页。
8. 同类页面沿用已确认的风格锚点；最后检查全稿缩略图和逐页效果。准备、派发、结果记录、组装与最终验证均有分段确认门槛，避免前面满意、后半段自行换风格。

分段确认的命令与旧项目启用方式见 [视觉检查点](skills/codex-ppt-editable/references/visual-checkpoints.md)。白底细框、蓝色箭头的示意图可使用 [紧凑工程线框风格](skills/codex-ppt-editable/references/engineering-flowcharts.md)。

用户原始图表不会交给模型重绘；原图内部的坐标、比例尺和已有标注仍属于图片。新增标题、正文、标签、数字结论与参考文献可直接修改。可读表格数据支持原生表格。不能把“可编辑”解释为原始图片中每个像素或标注均可单独编辑。

新绘制的框线、箭头和图形仍由图片模型生成，属于图片；简略示意图不代表改用代码绘制。新规格使用 schema_version=2 与 sample_slides 数组，旧项目的单页批准和图片来源保持兼容。详细接口见技能内的 references/deck-spec.md 与 references/intake-state.md。

## 依赖与运行

- Python 3.10+。
- 内置图片生成能力优先；API/CLI 是用户明确选择的备用路径。
- 核心组装依赖：python-pptx、Pillow、filelock。
- 可选预览：宿主自带渲染工具；或 LibreOffice + Poppler。Windows PowerPoint 可人工导出预览。
- API 备用依赖和模型配置见技能中的参考文档。密钥从环境或本地运行时配置读取，不放进仓库。

```sh
python skills/codex-ppt-editable/scripts/runtime.py doctor
python skills/codex-ppt-editable/scripts/runtime.py bootstrap
```

运行时缓存可用 `CODEX_PPT_EDITABLE_HOME` 指定。开发项目、缓存和输出路径由使用者配置，不绑定某一台机器。

## 独立使用示例与检查

从零制作请看 [v2 图解示例](examples/visual-planning/README.md)。`examples/minimal` 保留旧版原生对象示例及历史来源，不用作新项目启动模板。

旧 minimal 示例保留作为 v1 兼容样本。v2 的配图偏好、双样页及全稿验收命令见 [视觉规划指南](skills/codex-ppt-editable/references/visual-planning.md) 与 [检查流程](skills/codex-ppt-editable/references/quality-and-rendering.md)。用户 PPT、截图与私人验证文件不随仓库发布。

```sh
python -m unittest discover -s tests -v
```

离线测试使用明确标识的测试夹具，不会冒充图片模型生成结果；正式使用必须保留真实的生成来源记录。

## 来源与许可

上游固定版本及改动范围见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。保留原作者 MIT 声明；新增部分同样按 MIT 发布。此项目为社区衍生增强版，不代表上游作者或 OpenAI 官方。用户提供的模板、字体、品牌和图片的权利不因代码采用 MIT 而改变。
