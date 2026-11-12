$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$exe=Join-Path $root 'ChatGPTStartup.exe'
$key='HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
$expected='"'+$exe+'" --watch'
$task=Get-ScheduledTask -TaskName ChatGPTShinchanAnimation -ErrorAction SilentlyContinue
if($task -and @($task.Actions | Where-Object {$_.Execute -ine $exe}).Count){throw 'The startup task belongs to a different installation.'}
$current=Get-ItemProperty -LiteralPath $key -Name ChatGPTShinchanAnimation -ErrorAction SilentlyContinue
if($current -and $current.ChatGPTShinchanAnimation -eq $expected){Remove-ItemProperty -LiteralPath $key -Name ChatGPTShinchanAnimation}
if(Test-Path -LiteralPath $exe){Start-Process -FilePath $exe -ArgumentList '--stop' -WindowStyle Hidden -Wait}
if($task){Unregister-ScheduledTask -TaskName ChatGPTShinchanAnimation -Confirm:$false}
Write-Output 'Disabled the animation watcher. The system ChatGPT entry is unchanged.'
