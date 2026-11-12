ChatGPT 原入口 · 蜡笔小新敲键盘开场

使用方式：继续点击 Windows 原来的 ChatGPT 应用图标。
此版本监听本机 Windows 的窗口显示/恢复事件，对 OpenAI.Codex_2p2nqsd0c76g0 包的 ChatGPT.exe 主窗口播放动画。
仅在 ChatGPT 从未运行状态真正启动、首次出现主窗口时播放一次。已经在后台运行时，点击应用图标、从系统搜索/开始菜单唤回、最小化恢复、从托盘显示或新建窗口都不重复播放。
完全退出 ChatGPT 后再次启动会重新播放。监听程序启动时已在运行的 ChatGPT 会被记为已有会话，不补播动画。
按 Esc 或点开场右下角可跳过。
启动声音：用户选定的第二段台配原声“你回来了”，连续 5 秒，动画第 7 秒（还剩 5 秒时）开始播放，第 12 秒随动画收尾。前 7 秒不播放音乐。
此段直接取自同一原片 9.5–14.5 秒，保留原有配乐、环境声和台词，不循环、不另配音乐、不调速、不改变音高或音量。跳过或关闭动画立即停止声音。
原片来源：https://www.bilibili.com/video/BV1iy4y1n75m/?p=1（妈妈要死掉了1）。当前播放文件为 assets/startup-original.wav，记录见 assets/startup-original-source.json。

动画沿用 yanami-sec/codex-startup-animation-windows 的头像圆环、碎片散开、线稿显现、彩色画面和合拢转场。
人物使用用户选定的“墨镜敲电脑”小新，并将横版素材用于手指交替按键、轻微点头和镜片反光。
人物动态由画布局部网格形变绘制，不调用外部视频生成服务。

这一版本是覆盖在真实客户端窗口上的开场。动画结束后关闭覆盖层，交回原客户端。
它不会把壁纸注入官方页面。原项目的应用内背景功能仍保留在源码中，需要其另行支持的启动方式。

开场监听程序由当前用户的 Windows 登录任务自动启动，使用交互式用户会话和普通权限；失败后每分钟重试，最多 3 次。无网络访问、无端口、无聊天或页面内容读取。
仅播放期间创建 WebView2；素材、运行数据、日志和 WebView2 缓存均在安装目录的 .state 中（建议放到 D 盘）。
Windows 任务计划程序中保存 ChatGPTShinchanAnimation 登录任务，只指向此目录的程序。没有新增桌面或开始菜单图标。

Preview.cmd：播放一次预览，不打开或关闭 ChatGPT。
Enable.cmd：启用原入口动画。
Disable.cmd：关闭动画并移除本工具自己的登录任务和旧版启动项。
请在移动或删除此目录之前执行 Disable.cmd，在新位置执行 Enable.cmd。

来源：https://github.com/yanami-sec/codex-startup-animation-windows
基准提交：38bf68e（完整提交见源码仓库）
素材参考：https://www.pinterest.com/pin/292382200829331931/
横版素材经内置 imagegen 生成：保留墨镜、红衣、白色笔记本和粉色房间，扩展成16:9，保持二维动画线条，无界面文字。
遵循原仓库 THIRD_PARTY_NOTICES.md。原项目未指定开源许可证；本地改动不为上游代码或素材授予新许可。
运行需要 Windows 10/11、.NET Framework 4.8、已安装的 Microsoft Edge WebView2 Runtime。
