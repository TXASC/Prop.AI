# Remove PropAI scheduled tasks
Unregister-ScheduledTask -TaskName "PropAI-DailyFast" -Confirm:$false -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName "PropAI-WeeklyFull" -Confirm:$false -ErrorAction SilentlyContinue
