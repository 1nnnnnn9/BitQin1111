# 三页通用示例

主题“从想法到演示”，不是任何用户旧 PPT 的改版。标题、正文、标签与表格都是原生对象。底图由内置 image_gen 生成，不含文字。示例没有真实科研数据、品牌或个人资料。

## 从零执行

复制本目录到自己的工作目录。通过会话收集已知答案，用 intake.py update 记录；不要让脚本把缺失的用户答案自动设为已确认。下面的命令中，SKILL 是已安装技能目录：

1. python "$SKILL/scripts/intake.py" init --project .
2. 按 next 的结果确认模板、风格、素材、大纲与后端；将已知答案保存在 answers.json，用 update --answers answers.json 更新。大纲写成文件后，用 approve --stage outline --artifact outline.md 记录用户确认。
3. python "$SKILL/scripts/prepare_background_jobs.py" --spec deck_spec.json --sample-only 1
4. 派发并按 prompts/slide_01.json 调用内置图片工具，复制选定输出到项目，通过 record_slide_result.py 记录真实来源。
5. python "$SKILL/scripts/assemble_editable_ppt.py" --spec deck_spec.json --output sample.pptx --slides 1
6. 渲染、看图并交付 sample.pptx 和预览；用 intake.py sample 注册二者，用户确认后执行 approve --stage sample。
7. prepare_background_jobs.py --spec deck_spec.json 准备余下任务；完成、记录后组装完整 PPTX。

无模板时，已知答案的数据示例：

~~~json
{
  "template": "none",
  "style": "清爽专业风",
  "materials": [],
  "topic": "从想法到演示",
  "audience": "普通演示文稿使用者",
  "slide_count": 3,
  "backend": {"name": "built-in image tool", "confirmed": true}
}
~~~

模板输入可使用 template 路径或数组；检查后 style 记录为 {"name":"提取的风格","inspected":true,"preview":"代表页预览路径"}。不要在未观察预览时写 inspected=true。

## 已生成结果

本仓库附带维护者通用演示的真实底图和 demonstration.pptx，便于快速查看。生成提示词、来源摘要及验证结果在 validation.md。它们是验证独立技能的示例，不能冒充客户确认记录。正常制作仍需遵守样页确认流程。

图像背景不可逐像素编辑；所有新增文字与表格可编辑。图像文件中的内部内容仍属于图片。
