# Richtet eine Windows-Aufgabe ein, die "heavy auto" regelmäßig ausführt
# (Sync -> Progression -> Dashboard). Ausführen mit:
#   powershell -ExecutionPolicy Bypass -File .\install_task.ps1            (alle 2 Stunden)
#   powershell -ExecutionPolicy Bypass -File .\install_task.ps1 -Hours 1
#   powershell -ExecutionPolicy Bypass -File .\install_task.ps1 -Remove
param([int]$Hours = 2, [switch]$Remove)

$name = "Heavy Garmin Auto-Progression"
if ($Remove) {
    Unregister-ScheduledTask -TaskName $name -Confirm:$false
    Write-Host "Aufgabe '$name' entfernt."
    return
}
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = (Get-Command python).Source
$action = New-ScheduledTaskAction -Execute $python -Argument "-m heavy auto" -WorkingDirectory $dir
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(5) -RepetitionInterval (New-TimeSpan -Hours $Hours)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries
Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
Write-Host "Aufgabe '$name' eingerichtet: alle $Hours Stunde(n) 'python -m heavy auto' in $dir"
