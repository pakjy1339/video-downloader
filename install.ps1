# Video Downloader 설치 (윈도우)
#   powershell -ExecutionPolicy Bypass -c "irm https://raw.githubusercontent.com/pakjy1339/video-downloader/main/install.ps1 | iex"
# 관리자 권한 없이 내 계정에만 설치됩니다. 다시 실행하면 재설치(업데이트)됩니다.
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [Text.Encoding]::UTF8

$Repo  = 'pakjy1339/video-downloader'
$Dir   = if ($env:VD_INSTALL_DIR) { $env:VD_INSTALL_DIR } else { Join-Path $env:LOCALAPPDATA 'Programs\VideoDownloader' }
$UV    = Join-Path $env:USERPROFILE '.local\bin\uv.exe'
$Name  = 'Video Downloader'
$Port  = if ($env:VD_PORT) { $env:VD_PORT } else { '8765' }
function Say($t) { Write-Host "`n> $t" -ForegroundColor Red }

Say '1/5 설치 도구(uv) 준비'
if (-not (Test-Path $UV)) {
  $env:UV_NO_MODIFY_PATH = '1'
  Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
}

Say '2/5 다운로더 받기'
# 켜져 있던 다운로더가 있으면 끄기(다운로드 중이면 거절됨)
try { Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:$Port/api/quit" -ContentType 'application/json' -Body '{}' -TimeoutSec 3 | Out-Null; Start-Sleep 2 } catch {}
New-Item -ItemType Directory -Force $Dir | Out-Null
if ($env:VD_LOCAL_SRC) {   # 테스트용: GitHub 대신 로컬 폴더에서 복사
  Copy-Item -Path (Join-Path $env:VD_LOCAL_SRC '*') -Destination $Dir -Recurse -Force
} else {
  $Tmp = Join-Path $env:TEMP ("vd-" + [guid]::NewGuid())
  New-Item -ItemType Directory -Force $Tmp | Out-Null
  Invoke-WebRequest "https://github.com/$Repo/archive/refs/heads/main.zip" -OutFile "$Tmp\app.zip" -UseBasicParsing
  Expand-Archive "$Tmp\app.zip" -DestinationPath $Tmp -Force
  $Src = Get-ChildItem $Tmp -Directory | Where-Object { $_.Name -like '*-main' } | Select-Object -First 1
  Copy-Item -Path (Join-Path $Src.FullName '*') -Destination $Dir -Recurse -Force
  Remove-Item $Tmp -Recurse -Force
}

Say '3/5 Python·ffmpeg·yt-dlp 설치 (처음엔 1~3분 걸려요)'
& $UV venv --quiet --allow-existing --python 3.12 "$Dir\.venv"
if ($LASTEXITCODE -ne 0) { throw 'Python 준비 실패' }
& $UV pip install --quiet --python "$Dir\.venv\Scripts\python.exe" -U -r "$Dir\requirements.txt"
if ($LASTEXITCODE -ne 0) { throw '패키지 설치 실패' }

Say '4/5 바탕화면·시작 메뉴·자동 실행 바로가기'
$Pyw = "$Dir\.venv\Scripts\pythonw.exe"
$Sh  = New-Object -ComObject WScript.Shell
function Link($path, $arguments) {
  $s = $Sh.CreateShortcut($path)
  $s.TargetPath = $Pyw; $s.Arguments = $arguments; $s.WorkingDirectory = $Dir
  $s.IconLocation = "$Dir\icon.ico,0"; $s.Description = $Name; $s.Save()
}
$LinkDirs = @{}
foreach ($f in 'Desktop', 'Programs', 'Startup') {
  $LinkDirs[$f] = if ($env:VD_LINK_DIR) { Join-Path $env:VD_LINK_DIR $f } else { [Environment]::GetFolderPath($f) }   # VD_LINK_DIR: 테스트용
  New-Item -ItemType Directory -Force $LinkDirs[$f] | Out-Null
}
Link (Join-Path $LinkDirs.Desktop  "$Name.lnk") "`"$Dir\run.py`" --open"
Link (Join-Path $LinkDirs.Programs "$Name.lnk") "`"$Dir\run.py`" --open"
Link (Join-Path $LinkDirs.Startup  "$Name.lnk") "`"$Dir\run.py`""

Say '5/5 실행'
$OpenArg = if ($env:VD_LINK_DIR) { '' } else { ' --open' }   # 테스트 때는 브라우저를 띄우지 않음
Start-Process -FilePath $Pyw -ArgumentList "`"$Dir\run.py`"$OpenArg" -WorkingDirectory $Dir

Write-Host "`n설치 완료!" -ForegroundColor Green
Write-Host '- 다운로더 주소: http://127.0.0.1:8765  (즐겨찾기 해두세요)'
Write-Host "- 바탕화면의 '$Name' 아이콘으로 열 수 있어요. 오른쪽 클릭 > 작업 표시줄에 고정하면 편해요."
Write-Host '- 컴퓨터를 켜면 자동으로 실행되고, 켤 때마다 최신 버전으로 업데이트됩니다.'
