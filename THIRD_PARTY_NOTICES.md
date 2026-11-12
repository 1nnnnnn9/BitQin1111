# 第三方来源与修改说明

## codex-ppt-skill（MIT）

- 上游作者：ningzimu
- 上游仓库：https://github.com/ningzimu/codex-ppt-skill
- 固定版本：941dcafe2f23ea4ae61de99e9b22fb0ef3d9e06c（2026-10-13）
- 原版权声明：Copyright (c) 2026 ningzimu
- 许可证：MIT。完整许可保留于仓库 LICENSE 和技能目录 LICENSE。
- 本项目为独立社区衍生增强版，不表示原作者或 OpenAI 官方背书。

复用内容：

- 上游 skills/codex-ppt/references 下 12 份风格文档，移动到本技能 references/styles/。保留原内容，生成时只提取视觉语言，覆盖旧“图内文字”要求。
- image_gen.py 与 image_providers/：保留 API 备用提供者实现；image_gen.py 和 openai_compatible.py 改为独立缓存变量、独立依赖引导及有效的本项目配置文档。继承的默认模型标识不保证任一服务支持；备用模式须显式选择实际可用模型。
- record_slide_dispatch.py、record_slide_result.py、record_slide_blocker.py、slide_job_status.py、slide_run_state.py：保留逐页派发、结果哈希及状态记录机制。

其中 record_slide_dispatch.py、record_slide_result.py 和 slide_job_status.py 在本项目中增加分段视觉确认检查；原始来源与版权保留，修改标记和文件摘要见 upstream-provenance.json。新增 visual_checkpoints.py 负责本项目的代表页确认与风格锚点，不属于上游原始实现。

没有打包上游的整页图片组装器、旧运行时安装目录、私有凭证、字体或本机专用二进制。新增的模板/素材访谈、留白任务、原生 PPTX 组装、验证、预览适配、测试及文档由本项目编写。文件级来源与版本见技能内 upstream-provenance.json。

## Python 依赖

依赖按 requirements 文件安装，不将其二进制拷贝进技能。各依赖仍适用各自许可证；安装环境中的第三方 notices 不能由本项目 MIT 许可证替代。

## 用户素材与示例

本项目的 MIT 许可只覆盖本项目可许可的代码及资源，不重新授权用户提供的模板、照片、图表、品牌素材或字体。应保留相关归属与来源。

通用示例的无字背景由内置图片生成工具生成，提示词和来源摘要随示例记录，不包含真实实验结果或个人信息。它们用于展示与验证；图片生成并不意味着任何主体拥有排他版权。新增示例文字、布局规格及表格为本项目编写。

## ChatGPT 蜡笔小新启动动画

`projects/chatgpt-shinchan-startup/` 是单独收录的 Windows 启动动画定制。其上游启动动画代码没有指定开源许可证，角色图片和台配原声属于第三方素材；本仓库根目录的 MIT 许可不重新授权该目录。来源与 Microsoft WebView2 组件许可见该目录的 [第三方说明](projects/chatgpt-shinchan-startup/THIRD_PARTY_NOTICES.md) 和 [许可范围](projects/chatgpt-shinchan-startup/LICENSE.md)。
