# API/CLI 备用图片后端

仅在内置工具不可用、缺少所需能力或用户明确选择API/CLI时使用。先确认备用后端，再配置依赖：
```
python scripts/runtime.py bootstrap --api
```

所需环境变量：
- OPENAI_API_KEY：在用户本机配置，不要求贴到聊天中。
- OPENAI_BASE_URL：可选，使用用户选择的服务。
- CODEX_PPT_IMAGE_MODEL：使用该服务实际支持、用户选择的模型名称。
- CODEX_PPT_EDITABLE_HOME：可配置运行时目录；默认独立缓存，不读取原codex-ppt安装目录。

随包的image_gen.py和image_providers改编自固定上游版本，图像后端、生成/编辑、质量及来源记录原则保持一致。模型能力和参数以当前服务为准，不能因为上游默认字符串存在就宣称服务支持。

```
python scripts/image_gen.py generate --prompt-file PROMPT.txt --model YOUR_MODEL --out OUTPUT.png
```
需要参考图时先检查CLI帮助中的输入图参数，传入真实素材。API返回错误时保留错误和页码，不切到程序绘图。配置文件和密钥不得加入Git提交。
