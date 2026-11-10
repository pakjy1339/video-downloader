"""Video Downloader 실행기 (GitHub 설치판, 맥·윈도우 공용).

켤 때마다:
  1) 이미 켜져 있으면 → (--open이면) 브라우저만 열고 끝
  2) GitHub에 새 버전이 있으면 받아서 교체
  3) yt-dlp 등 최신으로 업데이트
  4) 다운로더 시작 (127.0.0.1:8765, 이 컴퓨터 안에서만)
기록: 같은 폴더의 downloader.log
"""
import io
import os
import runpy
import shutil
import subprocess
import sys
import time
import urllib.request
import webbrowser
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
URL = f"http://127.0.0.1:{os.environ.get('VD_PORT', '8765')}/"
OPEN = "--open" in sys.argv
NOWIN = getattr(subprocess, "CREATE_NO_WINDOW", 0)
KEEP = {".venv", "downloader.log", "team.key"}   # 업데이트할 때 건드리지 않는 것

logf = HERE / "downloader.log"
if logf.exists() and logf.stat().st_size > 1_000_000:
    logf.unlink()
log = open(logf, "a", encoding="utf-8", buffering=1)
sys.stdout = sys.stderr = log
print(f"\n===== {time.strftime('%Y-%m-%d %H:%M:%S')} start {' '.join(sys.argv[1:])}")

# 가상환경의 실행 파일(deno 등)을 찾을 수 있게
os.environ["PATH"] = str(Path(sys.executable).parent) + os.pathsep + os.environ.get("PATH", "")


def running():
    try:
        with urllib.request.urlopen(URL + "api/jobs", timeout=2):
            return True
    except Exception:
        return False


def get(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": "VideoDownloader-updater", "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def update_app():
    """GitHub의 VERSION이 다르면 저장소 전체를 받아서 덮어씀."""
    repo = (HERE / "REPO").read_text().strip()
    remote = get(f"https://raw.githubusercontent.com/{repo}/main/VERSION?t={int(time.time())}").decode().strip()
    local = (HERE / "VERSION").read_text().strip() if (HERE / "VERSION").exists() else ""
    if remote == local:
        print("app up to date:", local)
        return False
    print(f"updating app {local} -> {remote}")
    z = zipfile.ZipFile(io.BytesIO(get(f"https://github.com/{repo}/archive/refs/heads/main.zip", 60)))
    for m in z.infolist():
        rel = m.filename.split("/", 1)[1] if "/" in m.filename else ""
        if not rel or rel.split("/")[0] in KEEP:
            continue
        dest = HERE / rel
        if m.is_dir():
            dest.mkdir(parents=True, exist_ok=True)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(z.read(m))
    print("app updated")
    return True


def uv():
    for p in (shutil.which("uv"), Path.home() / ".local" / "bin" / ("uv.exe" if os.name == "nt" else "uv")):
        if p and Path(p).exists():
            return str(p)
    return None


def update_packages():
    """yt-dlp 등 최신으로(실패해도 진행)."""
    u = uv()
    cmd = ([u, "pip", "install", "-q", "--python", sys.executable] if u else [sys.executable, "-m", "pip", "install", "-q"])
    r = subprocess.run(cmd + ["-U", "-r", str(HERE / "requirements.txt")],
                       capture_output=True, text=True, timeout=300, creationflags=NOWIN)
    print("packages:", "ok" if r.returncode == 0 else r.stderr.strip()[-400:])


if running():
    print("already running")
    if OPEN:
        webbrowser.open(URL)
    sys.exit(0)

for step in (update_app, update_packages):
    try:
        step()
    except Exception as e:
        print(f"{step.__name__} skipped: {e}")

os.chdir(HERE)
sys.argv = [str(HERE / "server.py")] + ([] if OPEN else ["--no-browser"])
runpy.run_path(str(HERE / "server.py"), run_name="__main__")
