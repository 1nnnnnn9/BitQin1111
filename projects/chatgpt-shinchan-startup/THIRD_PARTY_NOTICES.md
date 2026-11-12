# 来源与第三方说明

## 启动动画代码

- 直接上游：https://github.com/yanami-sec/codex-startup-animation-windows
- 本地改造基准提交：38bf68e6a694c22d8bdc19e3c6d6d2b2d56979e6（基于该提交的 Windows 动画实现）。
- 更早来源：https://github.com/panding999/codex-startup-animation 和 https://github.com/paperfish-bot/codex-startup-animation 。
- 取得的上游版本没有指定开源许可证。本目录不重新授权这些代码，也不适用仓库根目录 MIT 许可。
- 本地改动：蜡笔小新人物与敲键盘动态、5 秒原片音频与延迟播放、官方原入口窗口覆盖层、按进程生命周期防止后台唤回重复播放、Windows 登录任务与验证脚本。

## 人物图片

- 用户选定的参考：https://www.pinterest.com/pin/292382200829331931/
- `assets/shinchan-wide.png` 使用内置图片生成能力，依据选定参考扩展横幅，保留墨镜、红衣、白色笔记本和粉色房间。
- 蜡笔小新角色及第三方原始美术的权利仍归相应权利人；图片生成不构成对角色版权的重新授权。头像与线稿来自本地用户选定素材。

## 台配原声

- 来源：https://www.bilibili.com/video/BV1iy4y1n75m/?p=1 （《妈妈要死掉了1》）。
- `assets/startup-original.wav` 为原片 9.5–14.5 秒连续 5 秒，含原有配乐和“你回来了”。只截取并解码为 PCM，没有另加配乐、循环、调速或改变音量。
- 不分发整集视频；详细时间与 SHA-256 见 `assets/startup-original-source.json`。
- 声音与角色权利归相应权利人，本仓库不为其授予额外权利。

## Microsoft WebView2

- 开发 SDK：Microsoft.Web.WebView2 1.0.4314.35。
- 运行包包含 SDK 的 Core / WinForms 程序集及 x64 WebView2Loader，用于承载本地动画；其许可及第三方通知完整保留于 `third-party/WebView2/`。
- 不包含 Microsoft Edge 或 WebView2 Runtime；需要另行安装运行时。

本工具为非官方本地定制，不由 OpenAI、Microsoft 或蜡笔小新权利人背书。不分发官方 ChatGPT/Codex 应用、账户数据、聊天记录或用户缓存。
