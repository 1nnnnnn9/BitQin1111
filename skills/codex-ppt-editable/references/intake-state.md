# 记录已知答案与确认

intake.py 不会向用户提问；它返回下一步，由执行代理结合会话提出问题或继续工作。不能用“脚本需要”为由让用户重复回答，也不能把缺失答案自动写为已确认。

~~~sh
python scripts/intake.py init --project PROJECT
python scripts/intake.py update --project PROJECT --answers known_answers.json
python scripts/intake.py next --project PROJECT
~~~

known_answers.json 只填已明确的信息：

- template：无模板为 "none"，有模板为路径、路径数组或附件描述。
- style：无模板时为用户选定的风格名；有模板时为 {"name":"提取风格","inspected":true,"preview":"已观察的代表页预览"}。
- materials：清点后的素材数组；明确无素材为 []，未问则不填。
- visual_preference：素材确认后单独询问，记录 schematic（简略示意图为主）、realistic（写实／三维图为主）或 mixed（按内容混合）。已有答案直接复用，不能从配色推断。
- topic、audience；slide_count 或 minutes 至少一项。
- backend：{"name":"built-in image tool","confirmed":true}，已有明确授权时直接记录。

更新主题、模板、风格或素材等关键输入会使旧大纲/样页确认失效；修改后端会使样页确认失效。文件状态记录的是实际会话决定，不能代替用户确认。

大纲已确认后：
~~~sh
python scripts/intake.py approve --project PROJECT --stage outline --artifact outline.md
~~~

新项目用 version=2，完整样稿包含两个声明的样页（单页任务为一个）。两页可编辑 PPTX 和逐页预览已交付后：
~~~sh
python scripts/intake.py sample --project PROJECT --pptx sample.pptx --slides 2 8 --preview sample-2.png sample-8.png
~~~

用户确认该样页后：
~~~sh
python scripts/intake.py approve --project PROJECT --stage sample
~~~

注册样页会检查它包含原生文本形状，但仍需视觉检查文字内容、留白和可编辑效果。样页不能只是一张背景图。不要把维护者的自动化测试确认视为客户的样页确认。

--slides 顺序必须等于 deck_spec.json 的 sample_slides，并按规格的页面顺序排列；预览按相同顺序对应。两页一起通过后记录一次 sample 确认。新注册样稿会撤销先前样稿批准。

旧 version=1 状态及其单页 sample_slide、preview 接口继续可读，已批准样稿与生成来源不被清除。继续旧项目时不自动补造配图答案；新增或重做页面前询问偏好，补齐视觉规划。需要完整升级时在保留旧项目副本后建立 v2 项目，不盲目修改旧来源记录。
