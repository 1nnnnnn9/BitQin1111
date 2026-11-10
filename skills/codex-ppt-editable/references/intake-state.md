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
- topic、audience；slide_count 或 minutes 至少一项。
- backend：{"name":"built-in image tool","confirmed":true}，已有明确授权时直接记录。

更新主题、模板、风格或素材等关键输入会使旧大纲/样页确认失效；修改后端会使样页确认失效。文件状态记录的是实际会话决定，不能代替用户确认。

大纲已确认后：
~~~sh
python scripts/intake.py approve --project PROJECT --stage outline --artifact outline.md
~~~

真正的单页可编辑 PPTX 和预览已交付后：
~~~sh
python scripts/intake.py sample --project PROJECT --pptx sample.pptx --preview sample.png
~~~

用户确认该样页后：
~~~sh
python scripts/intake.py approve --project PROJECT --stage sample
~~~

注册样页会检查它包含原生文本形状，但仍需视觉检查文字内容、留白和可编辑效果。样页不能只是一张背景图。不要把维护者的自动化测试确认视为客户的样页确认。
