# Video Downloader 제거 (윈도우). 받은 영상(다운로드 폴더)은 그대로 남습니다.
#   powershell -ExecutionPolicy Bypass -c "irm https://raw.githubusercontent.com/pakjy1339/video-downloader/main/uninstall.ps1 | iex"
$Dir  = if ($env:VD_INSTALL_DIR) { $env:VD_INSTALL_DIR } else { Join-Path $env:LOCALAPPDATA 'Programs\VideoDownloader' }
$Name = 'Video Downloader'
try { Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8765/api/quit' -ContentType 'application/json' -Body '{}' -TimeoutSec 3 | Out-Null; Start-Sleep 2 } catch {}
Get-CimInstance Win32_Process -Filter "Name='pythonw.exe'" | Where-Object { $_.CommandLine -like "*$Dir*" } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
foreach ($f in 'Desktop', 'Programs', 'Startup') {
  Remove-Item (Join-Path ([Environment]::GetFolderPath($f)) "$Name.lnk") -ErrorAction SilentlyContinue
}
Remove-Item $Dir -Recurse -Force -ErrorAction SilentlyContinue
Write-Host 'Video Downloader를 제거했습니다.'
