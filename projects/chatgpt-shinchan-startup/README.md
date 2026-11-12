# ChatGPT 原入口 · 蜡笔小新启动动画

Windows 本地定制：点击原来的 ChatGPT 应用图标，冷启动时播放约 12 秒开场，展示蜡笔小新敲键盘；第 7 秒开始播放用户选定的 5 秒台配原声“你回来了”。

![人物画面](assets/shinchan-wide.png)

## 下载使用

**[下载 Windows 即用包](https://github.com/1nnnnnn9/BitQin1111/raw/refs/heads/main/projects/chatgpt-shinchan-startup/downloads/ChatGPT-Shinchan-Windows.zip)**

1. 解压到固定目录，建议 `D:\Codex\Outputs\ChatGPT-Shinchan`。
2. 双击 `Preview.cmd`，先看一次含声音的预览。
3. 双击 `Enable.cmd`，注册当前用户的 Windows 登录任务。
4. 从托盘完全退出 ChatGPT 后，再点击原来的官方图标。

仅在应用从未运行状态启动时播放一次；应用已在后台运行、最小化恢复、托盘唤回或新建窗口时不重播。监听器启动时应用已运行，也不会补播。按 Esc 或点击跳过可结束开场并停止声音。

`Disable.cmd` 停止监听并移除本工具自己的登录任务。移动安装目录前先停用，在新目录重新启用。任务名为 `ChatGPTShinchanAnimation`；同一用户只启用一份安装。

## 环境与接入方式

- Windows 10/11 x64、.NET Framework 4.8，以及已安装的 Microsoft Edge WebView2 Runtime。
- 适配的官方进程名为 `ChatGPT.exe`，应用包家族为 `OpenAI.Codex_2p2nqsd0c76g0`。其他包名或未来应用版本需要调整匹配逻辑。
- 启动时短暂覆盖真实客户端窗口，结束后交回客户端。继续使用原来的系统应用入口，不创建新的桌面或开始菜单入口。
- 原声直接取自同一原片的连续 5 秒，保留原有配乐和环境声；不循环、不叠加其他音乐。动画前 7 秒静音。
- 素材、日志和 WebView2 缓存在安装目录内。监听器不读取聊天内容，不启用本地调试端口，不发送网络请求。

这是启动覆盖动画；不包含上游另一种启动方式的应用内壁纸注入功能。

## 从源码构建

开发 SDK 使用 `Microsoft.Web.WebView2 1.0.4314.35`，可从 [NuGet 官方包页面](https://www.nuget.org/packages/Microsoft.Web.WebView2/1.0.4314.35) 下载并解压到 D 盘。解压后的目录应包含 `lib/net462` 和 `runtimes/win-x64/native`。

在本目录运行：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\build-portable.ps1 -SdkRoot 'D:\Codex\Cache\WebView2-SDK\1.0.4314.35'
```

默认生成 `D:\Codex\Outputs\ChatGPT-Shinchan-Package` 和同名 ZIP；可用 `-Destination` 修改。编译使用 Windows 自带的 .NET Framework C# 编译器，不需要安装完整 Visual Studio。

## 验证

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\build-watcher.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\test-watcher.ps1
```

原生验证使用独立模拟窗口，检查冷启动、完全退出再启动、后台唤回防重播，以及原声在第 7 秒播放。不会关闭或重启真实 ChatGPT。

可选浏览器验证需要 Node.js 22+、Playwright 和 Microsoft Edge：

```powershell
npm install
npm run test:browser
```

本地验证记录：原声触发约为 7007 / 7004 毫秒，完整动画约 12 秒，后台唤回不重复播放。不同设备与后续官方版本仍可能影响行为。

## 来源

基于 [yanami-sec/codex-startup-animation-windows](https://github.com/yanami-sec/codex-startup-animation-windows) 改造。原声出处、人物参考与 WebView2 通知见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)，精确音频区间与摘要见 [原声记录](assets/startup-original-source.json)。

本目录不适用仓库根目录的 MIT 许可；上游未指定许可证的代码和第三方角色素材保留其原有权利。详见 [LICENSE.md](LICENSE.md)。
