#!/bin/bash
# Video Downloader 제거 (맥). 받은 영상(다운로드 폴더)은 그대로 남습니다.
#   curl -fsSL https://raw.githubusercontent.com/pakjy1339/video-downloader/main/uninstall.sh | bash
LABEL="com.videodownloader.app"
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
rm -f "$HOME/Library/LaunchAgents/$LABEL.plist"
rm -rf "$HOME/Applications/Video Downloader.app"
rm -rf "$HOME/Library/Application Support/VideoDownloader"
echo "Video Downloader를 제거했습니다."
