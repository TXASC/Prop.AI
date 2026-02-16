# Schedule PropAI tasks
$repoRoot = Resolve-Path "$PSScriptRoot\.."
$fastRunner = Join-Path $repoRoot "scripts\run_training_mode_fast.ps1"
$fullRunner = Join-Path $repoRoot "scripts\run_training_mode.ps1"

# Daily Fast Task
Register-ScheduledTask -TaskName "PropAI-DailyFast" -Trigger (New-ScheduledTaskTrigger -Daily -At 7:00am) -Action (New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -File $fastRunner") -RunLevel Highest -Force

# Weekly Full Task
Register-ScheduledTask -TaskName "PropAI-WeeklyFull" -Trigger (New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 8:00pm) -Action (New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -File $fullRunner") -RunLevel Highest -Force
