param([string]$SdkRoot='D:\Codex\Cache\WebView2-SDK\1.0.4314.35')
$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$build=Join-Path $repo '.build\native'
New-Item -ItemType Directory -Path $build -Force | Out-Null
foreach($name in @('Microsoft.Web.WebView2.Core.dll','Microsoft.Web.WebView2.WinForms.dll')){
 Copy-Item -LiteralPath (Join-Path $SdkRoot ('lib\net462\'+$name)) -Destination $build -Force
}
Copy-Item -LiteralPath (Join-Path $SdkRoot 'runtimes\win-x64\native\WebView2Loader.dll') -Destination $build -Force
$compiler=Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
& $compiler /nologo /target:winexe /platform:x64 /optimize+ /reference:System.dll /reference:System.Core.dll /reference:System.Windows.Forms.dll /reference:System.Drawing.dll ('/reference:'+(Join-Path $build 'Microsoft.Web.WebView2.Core.dll')) ('/reference:'+(Join-Path $build 'Microsoft.Web.WebView2.WinForms.dll')) ('/out:'+(Join-Path $build 'ChatGPTStartup.exe')) (Join-Path $repo 'windows\ShinchanWatcher.cs')
if($LASTEXITCODE -ne 0){throw 'Watcher compilation failed'}
Write-Output ('Built '+(Join-Path $build 'ChatGPTStartup.exe'))
