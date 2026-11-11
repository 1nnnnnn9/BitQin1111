# 新视觉部分先确认，再继续

初始样页通过，只批准这些样页展示过的视觉类型和版式。不能把“前几页可以”解释为允许后半段自由换样式。新项目默认启用 visual_checkpoints；旧 v2 项目继续制作前先 enable，只继承真实已批准样页的证据。

## 使用者看到的流程

1. 沿用已满意的页面作为风格锚点，继续制作同类、结构接近的页面。
2. 首次出现表格、流程图、图表、布局／工位、多图证据等新视觉部分时，只做一张完整可编辑代表页，提供 PPTX 和预览，等使用者确认后才继续。
3. 同类型出现明显不同的构图、密度、图形语言或图文组合，也登记新的 visual_variant 并停下来确认；配色相同不等于视觉已经满意。
4. 不满意时先总结问题，给2–3个符合既定约束的具体调整方向。例如“紧凑线框”“分组泳道”“拆分密集表格”，说明差异，不反复推荐已经拒绝的卡通或实物风格。
5. 选择方向不等于批准未看过的成品：按选择修改、展示新预览，明确满意后才继续。也接受新的参考图和自由文字意见。

相同风格和结构的后续页复用这次确认，不逐页重复问。当前一批图片 recorded 也不表示全稿完成；必须读 intake 的下一步。

## 命令

这些脚本只记录真实会话决定，不会替用户确认：

```sh
python scripts/visual_checkpoints.py enable --project PROJECT
python scripts/intake.py next --project PROJECT
```

新项目 init 已自动启用，无需重复 enable。旧项目缺失样页证据时先恢复，不能自动批准未展示的后半段。

双样页之后，next 返回 approved_prefix 和下一个检查点。prepare 默认只准备已批准的当前部分。新视觉代表页 N 使用：

```sh
python scripts/prepare_background_jobs.py --spec PROJECT/deck_spec.json --checkpoint-only N
```

记录真实图片派发、生成与结果后，只组装这一页并渲染：

```sh
python scripts/assemble_editable_ppt.py --spec PROJECT/deck_spec.json --output PROJECT/checkpoint-N.pptx --slides N
python scripts/visual_checkpoints.py register --project PROJECT --slide N --pptx checkpoint-N.pptx --preview checkpoint-N.png
```

交付当前代表页并得到使用者明确确认后：

```sh
python scripts/visual_checkpoints.py approve --project PROJECT --slide N
```

不满意时，将向使用者展示的2–3个方向保存为 options.json，例如：

```json
[
  {"id":"A","label":"紧凑摘要表","description":"保留关键列，详细值移到后页"},
  {"id":"B","label":"分组对照表","description":"按比较对象分组，用少量强调突出差异"}
]
```

```sh
python scripts/visual_checkpoints.py reject --project PROJECT --slide N --reason "用户指出的具体问题" --options options.json
python scripts/visual_checkpoints.py choose --project PROJECT --slide N --option A
```

choose 仅记录方向。修改并重新渲染后再 register、展示和确认；未改变的拒绝稿不能充当修订稿。需要重画背景时用 reset_slide.py 归档来源；重置代表页会撤销该视觉类别批准。

## 类型、变化与风格锚点

- 脚本从 visual_plan.form、实际 tables/images 推导类型，图解加表格也识别为新组合。
- 线性、分支合流、有组框流程分别识别；表格列数、短／中／密集行数区间、较小字号与配色处理也参与分类。图表通过 chart_type 区分柱状、折线等表现。
- 自动结构分类不能判断所有审美差异。执行代理还须识别同类型的明显变化，填写 visual_plan.visual_variant，如 summary-table、comparison-matrix、dense-table、diagram-with-table，不能为了绕过确认使用笼统名称。
- section 可记录章节名用于展示。仅换章节标题而视觉相同，可继续；新类型或明显变式必须暂停。
- 已批准完整页的不可变预览作为后续绘图锚点，延续整体配色、标题层次和图形语言；不复制旧内容、数字或表格单元格。更换代表页、风格或损坏证据后重新确认。
- 准备、派发、结果记录、组装和最终验证都有门禁；旧项目中提前准备的后页不能绕过检查点派发。

维护者测试的 synthetic 夹具和测试批准，不属于任何客户确认。此流程不改变“图片工具画非文字，原生文字后叠”的实现。
