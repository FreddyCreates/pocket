# Remove POCKET Desktop shortcuts for current user
Remove-Item -Force -ErrorAction SilentlyContinue "C:\Users\Medin\OneDrive\Desktop\POCKET Desktop.lnk"
Remove-Item -Force -ErrorAction SilentlyContinue "C:\Users\Medin\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\POCKET Desktop.lnk"
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue "C:\Users\Medin\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\POCKET"
Write-Host "POCKET Desktop shortcuts removed. Runtime files under ~/.pocket kept."
