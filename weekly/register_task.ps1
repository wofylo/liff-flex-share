param(
    [string]$Time = "18:50",
    [string]$TaskName = "WeeklyMeetingCard"
)
$ErrorActionPreference = "Stop"
$script = Join-Path $PSScriptRoot "weekly_card.py"
$python = (Get-Command python -ErrorAction Stop).Source
$action = New-ScheduledTaskAction -Execute $python -Argument "`"$script`"" -WorkingDirectory $PSScriptRoot
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Thursday -At $Time
$settings = New-ScheduledTaskSettingsSet -WakeToRun -StartWhenAvailable -AllowStartIfOnBatteries
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings `
    -Description "Open LIFF share tool with this week's meeting card" -Force | Out-Null
Get-ScheduledTask -TaskName $TaskName | Select-Object TaskName, State
