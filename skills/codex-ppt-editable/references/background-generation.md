# 无字背景与 codex-ppt 生成流程

## 内置工具优先

先确认宿主是否提供图片生成工具。使用真实可调用的内置后端；不把订阅、代理名或一张成功图片当成特定模型/质量参数的证明。工具未暴露的模型、尺寸或质量记录为 built-in default。API/CLI 需用户明确选择，禁止为方便保存路径悄悄切换。

完整样页的合同包括：背景生成工具/模式、输入图准备、提示词路径、输出原始路径、后端标签、最终背景文件与完整可编辑样页。全稿沿用该合同。

## 提示词

所有新绘制背景、图示与装饰图标都走图片后端。图可融合；文字区必须真实空白。每页提供：
- 画布比例与统一风格；
- 场景/示意内容，避免伪造实验图；
- 标题、正文、标签和素材窗口的坐标留白；
- 不得出现文字、数字、伪字、页码或脚注；
- 用户图表/Logo需保持原样，由组装层直接放入的说明。

风格参考仅用于视觉语言。不要把风格页的正文、旧题目或旧布局机械复制到新页。工具若支持明确输入图，按其工具说明传入；本地输入先查看。新图生成或编辑模式由样页实际方法决定，不虚构参数。

## 状态脚本

先由 intake.py 完成模板/风格/素材/大纲确认；样页前仅运行 prepare_background_jobs.py --sample-only N。样页实际生成后记录派发和结果，用 assemble_editable_ppt.py --slides N 组装，渲染后请用户确认。

用户确认后记录样页并运行 prepare_background_jobs.py 生成剩余任务。示例：
```
python scripts/record_slide_dispatch.py PROJECT --slide slide_02 --agent-id ACTUAL_ID --prompt-file prompts/slide_02.json
python scripts/record_slide_result.py PROJECT --slide slide_02 --agent-id ACTUAL_ID --backend-used "built-in image tool" --selected-source ORIGINAL_GENERATED.png --qa-note "实际检查结论"
```
一个子代理只处理一个任务。主代理保存真实生成输出并记录结果。顺序模式 agent-id 为 main。不要手改完成状态。

中文、符号或伪字残留时用原后端修复或重生成，不能用白块掩盖再声称原图无字。重复修复仍失败时报告阻塞，而非无限重试。
