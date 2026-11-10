#!/bin/bash
# Video Downloader 설치 (맥)
#   curl -fsSL https://raw.githubusercontent.com/pakjy1339/video-downloader/main/install.sh | bash
# 관리자 비밀번호 없이 내 계정에만 설치됩니다. 다시 실행하면 재설치(업데이트)됩니다.
set -euo pipefail

REPO="pakjy1339/video-downloader"
DIR="$HOME/Library/Application Support/VideoDownloader"
LABEL="com.videodownloader.app"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
APP="$HOME/Applications/Video Downloader.app"
UV="$HOME/.local/bin/uv"

say() { printf "\n\033[1;31m▶\033[0m %s\n" "$1"; }

say "1/5 설치 도구(uv) 준비"
if [ ! -x "$UV" ]; then
  curl -LsSf https://astral.sh/uv/install.sh | env UV_NO_MODIFY_PATH=1 sh
fi

say "2/5 다운로더 받기"
TMP="$(mktemp -d)"
curl -fsSL "https://github.com/$REPO/archive/refs/heads/main.zip" -o "$TMP/app.zip"
unzip -q "$TMP/app.zip" -d "$TMP"
mkdir -p "$DIR"
cp -R "$TMP"/*-main/. "$DIR/"
rm -rf "$TMP"

say "3/5 Python·ffmpeg·yt-dlp 설치 (처음엔 1~3분 걸려요)"
"$UV" venv --quiet --allow-existing --python 3.12 "$DIR/.venv"
"$UV" pip install --quiet --python "$DIR/.venv/bin/python" -U -r "$DIR/requirements.txt"

say "4/5 로그인할 때 자동 실행 설정"
mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key><array>
    <string>$DIR/.venv/bin/python</string><string>$DIR/run.py</string>
  </array>
  <key>WorkingDirectory</key><string>$DIR</string>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><dict><key>SuccessfulExit</key><false/></dict>
  <key>ThrottleInterval</key><integer>30</integer>
</dict></plist>
EOF
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"

say "5/5 응용 프로그램에 'Video Downloader' 추가"
mkdir -p "$HOME/Applications"
rm -rf "$APP"
osacompile -o "$APP" -e "do shell script \"launchctl kickstart gui/$(id -u)/$LABEL >/dev/null 2>&1 || true\"" \
                     -e "delay 1" -e "open location \"http://127.0.0.1:8765\""
# 아이콘
ICONSET="$(mktemp -d)/icon.iconset"; mkdir -p "$ICONSET"
for s in 16 32 128 256 512; do
  sips -z $s $s "$DIR/icon.png" --out "$ICONSET/icon_${s}x${s}.png" >/dev/null
  d=$((s*2)); [ $d -le 512 ] && sips -z $d $d "$DIR/icon.png" --out "$ICONSET/icon_${s}x${s}@2x.png" >/dev/null
done
iconutil -c icns "$ICONSET" -o "$APP/Contents/Resources/applet.icns" && touch "$APP"

# 켜질 때까지 기다렸다가 열기
for i in $(seq 1 90); do
  curl -s -o /dev/null http://127.0.0.1:8765/api/jobs && break
  sleep 2
done
open "http://127.0.0.1:8765"

printf "\n\033[1;32m설치 완료!\033[0m\n"
echo "- 다운로더 주소: http://127.0.0.1:8765  (북마크해 두세요)"
echo "- 다시 열 때: Spotlight(⌘ Space)에서 'Video Downloader' 검색. (위치: 홈 폴더 > 응용 프로그램)"
echo "- 맥을 켜면 자동으로 실행되고, 켤 때마다 최신 버전으로 업데이트됩니다."
