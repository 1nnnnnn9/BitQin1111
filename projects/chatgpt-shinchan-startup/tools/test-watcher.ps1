$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$build=Join-Path $repo '.build\native'
$fixture=Join-Path $build 'WatcherFixture.exe'
$compiler=Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
& $compiler /nologo /target:winexe /platform:x64 /reference:System.Windows.Forms.dll /reference:System.Drawing.dll ('/out:'+$fixture) (Join-Path $repo 'windows\WatcherFixture.cs')
if($LASTEXITCODE -ne 0){throw 'Fixture compilation failed'}
$state=Join-Path $repo ('.build\watcher-test-state-'+[DateTime]::Now.ToString('yyyyMMddHHmmss'))
$arguments=@('--watch','--fixture',('"'+$fixture+'"'),'--state',('"'+$state+'"'),'--watch-ms','42000')
$watcher=Start-Process -FilePath (Join-Path $build 'ChatGPTStartup.exe') -ArgumentList $arguments -WindowStyle Hidden -PassThru
try{
 Start-Sleep -Milliseconds 800
 $child=Start-Process -FilePath $fixture -ArgumentList '--exercise-reactivation','--duration-ms','22000' -WindowStyle Hidden -PassThru
 if(!$child.WaitForExit(25000)){throw 'First fixture did not exit'}
 # Fully exiting and relaunching must play again, even without a long idle gap.
 $child=Start-Process -FilePath $fixture -ArgumentList '--duration-ms','15000' -WindowStyle Hidden -PassThru
 if(!$child.WaitForExit(18000)){throw 'Relaunched fixture did not exit'}
 if(!$watcher.WaitForExit(10000)){throw 'Watcher did not exit'}
 $log=Get-Content -LiteralPath (Join-Path $state 'watcher.log') -Raw
 if($log -notmatch 'original-entry-animation-playing' -or $log -notmatch 'animation-complete'){throw ('Native event/player test failed: '+$log)}
 if($log -match 'player-error|message-error|fatal|script-error|navigation-success=False'){throw $log}
 if($log -notmatch 'original-entry-animation-playing visible=True' -or $log -notmatch 'animation-complete playback-ms=12\d{3}'){throw ('Visible full-duration playback was not verified: '+$log)}
 if(@([regex]::Matches($log,'original-entry-animation-playing')).Count -ne 2){throw ('Expected exactly one animation per process lifetime, including quit/relaunch: '+$log)}
 $audioCues=@([regex]::Matches($log,'startup-original-started playback-ms=(\d+)'))
 if($audioCues.Count -ne 2){throw ('Expected the selected original audio once per cold launch: '+$log)}
 foreach($cue in $audioCues){$ms=[int]$cue.Groups[1].Value;if($ms -lt 7000 -or $ms -ge 7300){throw ('Original audio must start at 7 seconds: '+$log)}}
 if($log -match 'startup-ambience-started|sound-load-failed|sound-play-failed'){throw ('Unexpected soundtrack or audio failure: '+$log)}
 if($log -notmatch 'activation-ignored app-session-already-running'){throw ('Window recreation did not exercise the existing-session gate: '+$log)}
 Write-Output 'PASS: cold launch and full quit/relaunch each play once; minimize/restore, hide/show, extra windows and window recreation do not replay.'
 Write-Output $log
}finally{
 if(!$watcher.HasExited){Start-Process -FilePath (Join-Path $build 'ChatGPTStartup.exe') -ArgumentList '--stop','--fixture',('"'+$fixture+'"') -WindowStyle Hidden -Wait}
}

# A background process already running when the helper starts must never get a
# delayed splash, even if its first visible window is shown after hook setup.
$seededState=$state+'-existing'
$child=Start-Process -FilePath $fixture -ArgumentList '--duration-ms','8000' -WindowStyle Hidden -PassThru
Start-Sleep -Milliseconds 400
$watcher=Start-Process -FilePath (Join-Path $build 'ChatGPTStartup.exe') -ArgumentList '--watch','--fixture',('"'+$fixture+'"'),'--state',('"'+$seededState+'"'),'--watch-ms','6500' -WindowStyle Hidden -PassThru
try{
 if(!$watcher.WaitForExit(10000)){throw 'Seeded watcher did not exit'}
 $child.WaitForExit(10000)|Out-Null
 $log=Get-Content -LiteralPath (Join-Path $seededState 'watcher.log') -Raw
 if($log -notmatch 'existing-app-session-seeded' -or $log -match 'original-entry-animation-playing|cold-start-detected|player-host-visible'){throw ('Existing background session incorrectly played an animation: '+$log)}
 if($log -match 'fatal|player-error'){throw $log}
 Write-Output 'PASS: restarting the helper while the app is already running does not play an animation.'
 Write-Output $log
}finally{
 if(!$watcher.HasExited){Start-Process -FilePath (Join-Path $build 'ChatGPTStartup.exe') -ArgumentList '--stop','--fixture',('"'+$fixture+'"') -WindowStyle Hidden -Wait}
}
