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

先由 intake.py 完成模板/风格/素材/配图偏好/大纲确认；新项目读取 visual-planning.md 并填写逐页 visual_plan。样页前仅运行 prepare_background_jobs.py --sample-only 2 8（编号等于声明的 sample_slides）。样页实际生成后记录派发和结果，用 assemble_editable_ppt.py --slides 2 8 组装双样页，渲染后请用户一次确认。单页任务仅传一个编号。

用户确认后记录样页。新项目再由 intake.py next 判断当前已批准部分及下一视觉检查点；prepare_background_jobs.py 仅准备当前获准部分。首次新类型／明显变式使用 --checkpoint-only N，只生成并交付该代表页，确认前不批量生成后续。旧 v2 项目先启用检查点；细节见 visual-checkpoints.md。示例：
```
python scripts/record_slide_dispatch.py PROJECT --slide slide_02 --agent-id ACTUAL_ID --prompt-file prompts/slide_02.json
python scripts/record_slide_result.py PROJECT --slide slide_02 --agent-id ACTUAL_ID --backend-used "built-in image tool" --selected-source ORIGINAL_GENERATED.png --qa-note "实际检查结论"
```
一个子代理只处理一个任务。主代理保存真实生成输出并记录结果。顺序模式 agent-id 为 main。不要手改完成状态。

中文、符号或伪字残留时用原后端修复或重生成，不能用白块掩盖再声称原图无字。重复修复仍失败时报告阻塞，而非无限重试。

需要更改已派发／记录的画面时，先运行 `reset_slide.py --project PROJECT --slide 3 --reason "具体修复原因"`。脚本归档旧任务、图片和来源，再把该页返回 pending；修改规格后重新 prepare、派发、用同一后端生成并记录。重做样页会撤销样页批准，需重新交付确认；不手改完成状态或覆盖来源。

已确认样页的原生文字位置可以调整。展开全稿任务时，如仅留白矩形改变，脚本保留样页原始生成提示词和图片来源，并单独记录确认后的文字位置；改变画面内容、风格、输入图或后端仍需重新生成。

v2 任务把配图偏好、节点几何与连接写入提示词，不发送原生标签字符串；模板风格与 scene_brief 不应覆盖 visual_plan 的关系要求。标签矩形内留白，框线画在外侧，箭头沿计划的节点关系连接。不要对解释性页面使用“禁止所有示意图／箭头”的通用空白母版提示词。正文和表格窗口不得挤占主图，冲突时先调整布局。
