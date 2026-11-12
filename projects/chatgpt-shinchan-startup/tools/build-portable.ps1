param(
 [string]$SdkRoot='D:\Codex\Cache\WebView2-SDK\1.0.4314.35',
 [string]$Destination='D:\Codex\Outputs\ChatGPT-Shinchan-Package'
)
$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$destinationPath=[IO.Path]::GetFullPath($Destination)
if($destinationPath -eq $repo -or $destinationPath.StartsWith($repo+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Use a destination outside the source tree.'}
& (Join-Path $PSScriptRoot 'build-watcher.ps1') -SdkRoot $SdkRoot
New-Item -ItemType Directory -Path $destinationPath -Force | Out-Null
foreach($name in @('ChatGPTStartup.exe','Microsoft.Web.WebView2.Core.dll','Microsoft.Web.WebView2.WinForms.dll','WebView2Loader.dll')){
 Copy-Item -LiteralPath (Join-Path $repo ('.build\native\'+$name)) -Destination $destinationPath -Force
}
foreach($name in @('animation.js','image-settings.js','shinchan-motion.js','index.html','style.css','Preview.cmd','Enable.cmd','Disable.cmd','README.md','README-SHINCHAN.txt','LICENSE.md','THIRD_PARTY_NOTICES.md')){
 Copy-Item -LiteralPath (Join-Path $repo $name) -Destination $destinationPath -Force
}
foreach($folder in @('assets','third-party')){
 Copy-Item -LiteralPath (Join-Path $repo $folder) -Destination $destinationPath -Recurse -Force
}
$runtimeTools=Join-Path $destinationPath 'tools'
New-Item -ItemType Directory -Path $runtimeTools -Force | Out-Null
foreach($name in @('install-original-entry.ps1','disable-original-entry.ps1')){
 Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination $runtimeTools -Force
}
# Explicit input list excludes logs and WebView2 state from an existing folder.
$items=@('ChatGPTStartup.exe','Microsoft.Web.WebView2.Core.dll','Microsoft.Web.WebView2.WinForms.dll','WebView2Loader.dll','animation.js','image-settings.js','shinchan-motion.js','index.html','style.css','Preview.cmd','Enable.cmd','Disable.cmd','README.md','README-SHINCHAN.txt','LICENSE.md','THIRD_PARTY_NOTICES.md','assets','third-party','tools') | ForEach-Object {Join-Path $destinationPath $_}
Compress-Archive -LiteralPath $items -DestinationPath ($destinationPath+'.zip') -Force
Write-Output ('Built portable package: '+$destinationPath+'.zip')
