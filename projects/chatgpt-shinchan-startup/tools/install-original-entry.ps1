$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$exe=Join-Path $root 'ChatGPTStartup.exe'
if(!(Test-Path -LiteralPath $exe)){throw 'ChatGPTStartup.exe is missing'}
$taskName='ChatGPTShinchanAnimation'
$existing=Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if($existing -and @($existing.Actions | Where-Object {$_.Execute -ine $exe}).Count){throw 'An animation startup task points at a different installation.'}
$identity=[System.Security.Principal.WindowsIdentity]::GetCurrent()
$trigger=New-ScheduledTaskTrigger -AtLogOn -User $identity.User.Value
$action=New-ScheduledTaskAction -Execute $exe -Argument '--watch' -WorkingDirectory $root
$principal=New-ScheduledTaskPrincipal -UserId $identity.User.Value -LogonType Interactive -RunLevel Limited
$settings=New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description 'Start the local ChatGPT Shinchan animation listener in the signed-in user session.' -Force | Out-Null
# Retire only the old Run value owned by this installation after registration succeeds.
$key='HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
$old=Get-ItemProperty -LiteralPath $key -Name $taskName -ErrorAction SilentlyContinue
if($old -and $old.$taskName -eq ('"'+$exe+'" --watch')){Remove-ItemProperty -LiteralPath $key -Name $taskName}
Start-ScheduledTask -TaskName $taskName
$state=Join-Path $root '.state'
New-Item -ItemType Directory -Path $state -Force | Out-Null
Export-ScheduledTask -TaskName $taskName | Set-Content -LiteralPath (Join-Path $state 'startup-task.xml') -Encoding UTF8
Write-Output 'Enabled: interactive user logon task, automatic restart on failure, existing ChatGPT entry preserved.'
