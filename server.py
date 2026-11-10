"""내 영상 다운로더 - 로컬 서버 (yt-dlp + ffmpeg)"""
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
import uuid
import webbrowser
from urllib.parse import urlparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import yt_dlp

HOST, PORT = "127.0.0.1", int(os.environ.get("VD_PORT", 8765))
TEAM = "--team" in sys.argv            # 팀 공유: 사무실 네트워크의 다른 PC도 접속 가능
BIND = "0.0.0.0" if TEAM else HOST
BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))   # exe로 묶였을 때는 내부 폴더
SAVE_DIR = Path.home() / "Downloads" / "VideoDownloader"
SAVE_DIR.mkdir(parents=True, exist_ok=True)
# 팀원 다운로드는 내 다운로드 폴더가 아니라 임시 폴더에 → 팀원 컴퓨터로 전달되면 바로 삭제
import tempfile
TEAM_DIR = Path(tempfile.gettempdir()) / "VideoDownloader-team"
TEAM_KEEP_HOURS = 6   # 팀원이 끝내 안 받아가면 이 시간 뒤 삭제
LOCAL_IPS = ("127.0.0.1", "::1")


def clean_team_dir(max_age_h=TEAM_KEEP_HOURS):
    if not TEAM_DIR.exists():
        return
    cutoff = time.time() - max_age_h * 3600
    for d in TEAM_DIR.iterdir():
        try:
            if d.stat().st_mtime < cutoff:
                shutil.rmtree(d, ignore_errors=True)
        except OSError:
            pass


def _cleaner():
    while True:
        time.sleep(1800)
        clean_team_dir()


def team_key():
    """팀 링크에 붙는 비밀 키(처음 한 번 만들어 저장). 키가 없는 다른 PC는 접속 불가."""
    f = BASE_DIR / "team.key"
    try:
        k = f.read_text().strip()
        if k:
            return k
    except OSError:
        pass
    import secrets
    k = secrets.token_urlsafe(9)
    f.write_text(k)
    return k


KEY = team_key()


def guide_url():
    """Guide 버튼 주소: 팀 서버면 /guide, 각자 설치한 버전이면 GitHub 안내 페이지."""
    if (BASE_DIR / "guide.html").exists():
        return "/guide"
    try:
        repo = (BASE_DIR / "REPO").read_text().strip()
        return f"https://github.com/{repo}#readme" if repo else ""
    except OSError:
        return ""


def lan_ip():
    """사무실 네트워크에서 이 PC의 주소."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("192.168.0.1", 9))   # 실제로 보내지 않음, 경로만 확인
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"

JOBS = {}
THUMBS = {}
LOCK = threading.Lock()


def find_ffmpeg():
    """시스템 ffmpeg → 없으면 파이썬 패키지(imageio-ffmpeg)에 들어 있는 ffmpeg."""
    p = shutil.which("ffmpeg")
    if p:
        return p
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


FFMPEG = find_ffmpeg()
IS_MAC = sys.platform == "darwin"


def base_opts():
    opts = {"quiet": True, "no_warnings": True, "noprogress": True}
    if os.path.isabs(FFMPEG):
        opts["ffmpeg_location"] = FFMPEG
    # 유튜브용 자바스크립트 실행기: node가 있으면 node, 없으면 deno(파이썬 패키지로 설치됨)
    if shutil.which("node"):
        opts["js_runtimes"] = {"node": {}}
    elif shutil.which("deno"):
        opts["js_runtimes"] = {"deno": {"path": shutil.which("deno")}}
    return opts


def fix_url(url):
    """vimeo.com 일반 링크는 로그인을 요구하므로 플레이어 주소로 바꿈."""
    m = re.match(r"https?://(?:www\.)?vimeo\.com/(?:channels/[^/]+/|showcase/\d+/video/)?(\d+)(?:/([0-9a-f]+))?", url)
    if m:
        return f"https://player.vimeo.com/video/{m[1]}" + (f"?h={m[2]}" if m[2] else "")
    # 다른 사이트에 삽입된 플레이어 주소에는 재생 옵션(?autoplay=…&app_id=…)이 붙어 있고, 이러면 비메오가 401로 거부함
    # → 비공개 링크 키(h)만 남기고 정리
    m = re.match(r"(?:https?:)?//player\.vimeo\.com/video/(\d+)/?(?:\?(.*))?$", url)
    if m:
        h = re.search(r"(?:^|&)h=([0-9a-f]+)", m[2] or "")
        return f"https://player.vimeo.com/video/{m[1]}" + (f"?h={h[1]}" if h else "")
    return url


ANSI = re.compile(r"\x1b\[[0-9;]*m")


def friendly_error(e):
    """yt-dlp 오류를 짧고 알아보기 쉬운 문장으로."""
    msg = ANSI.sub("", str(e)).strip()
    low = msg.lower()
    if "private video" in low:
        return "Private video. Only people the owner shared it with can watch it."
    if "[vimeo]" in low and ("401" in low or "403" in low):
        return "Vimeo refused this video. It's private or limited by its owner."
    if "sign in to confirm your age" in low or "age-restricted" in low:
        return "Age-restricted video. It needs a signed-in account."
    if "video unavailable" in low or "has been removed" in low:
        return "This video is unavailable or was removed."
    msg = re.sub(r"^ERROR:\s*", "", msg)
    msg = re.sub(r"\s*(See|Also see)\s+https?://\S+.*$", "", msg, flags=re.S)
    return msg[:300]


PIN_RE = re.compile(r"^https?://(?:[\w-]+\.)?pinterest\.[a-z.]+/pin/(?:[^/?#]*--)?(\d+)", re.I)


def expand_pinterest(url):
    """여러 장짜리(캐러셀) 핀이면 영상 목록을, 아니면 None(→ yt-dlp가 처리)을 돌려줌."""
    if re.match(r"^https?://pin\.it/\w+", url):
        req = urllib.request.Request(url, headers={"User-Agent": BROWSER_UA})
        with urllib.request.urlopen(req, timeout=10) as r:
            url = r.geturl()
    m = PIN_RE.match(url)
    if not m:
        return None
    data = json.dumps({"options": {"field_set_key": "unauth_react_main_pin", "id": m[1]}})
    req = urllib.request.Request(
        "https://www.pinterest.com/resource/PinResource/get/?data=" + urllib.parse.quote(data),
        headers={"User-Agent": BROWSER_UA, "X-Pinterest-PWS-Handler": "www/[username].js"})
    with urllib.request.urlopen(req, timeout=15) as r:
        d = json.load(r)["resource_response"]["data"]
    def best(video_list):
        """여러 화질 중 가장 큰 것(mp4 우선, 없으면 스트리밍 주소)."""
        vl = [v for v in (video_list or {}).values() if isinstance(v, dict) and v.get("url")]
        vl.sort(key=lambda v: ((v.get("height") or 0) * (v.get("width") or 0), v["url"].endswith(".mp4")), reverse=True)
        return vl[0]["url"] if vl else None

    vids = []
    # 1) 여러 장짜리(캐러셀) 핀
    for s in (d.get("carousel_data") or {}).get("carousel_slots") or []:
        u = best((s.get("videos") or {}).get("video_list"))
        if u:
            vids.append(u)
    # 2) 스토리(아이디어) 핀: 여러 페이지에 영상이 하나씩 있을 수 있음
    for page in (d.get("story_pin_data") or {}).get("pages") or []:
        for b in page.get("blocks") or []:
            u = best((b.get("video") or {}).get("video_list"))
            if u:
                vids.append(u)
    # 3) 다른 사이트 영상을 저장한 핀(비메오·유튜브 등): 삽입 주소 또는 원래 링크
    if not vids and not d.get("videos"):
        src = (d.get("embed") or {}).get("src") or ""
        link = d.get("link") or ""
        for u in (src, link):
            if re.search(r"(vimeo\.com|youtube\.com|youtu\.be|dailymotion\.com|tiktok\.com|instagram\.com|wistia|loom\.com|streamable\.com|twitch\.tv|x\.com|twitter\.com)/", u):
                vids.append(fix_url(re.sub(r"^http://", "https://", u)))
                break
    if not vids:
        return None   # 일반 영상 핀 → yt-dlp가 그대로 처리
    desc = (d.get("description") or "").strip()
    if len(desc) > 80:
        desc = desc[:80].rsplit(" ", 1)[0]
    seo = (d.get("seo_title") or "").split(" | ")[0].strip()
    title = (d.get("title") or d.get("grid_title") or desc or seo or "Pinterest pin").strip()
    imgs = d.get("images") or {}
    img = (imgs.get("orig") or imgs.get("736x") or imgs.get("474x") or {}).get("url", "")
    return {"t": title, "img": img, "site": "Pinterest",
            "v": [[u, f"{title} {i + 1}" if len(vids) > 1 else title] for i, u in enumerate(vids)]}


TVCF_RE = re.compile(r"^https?://(?:www\.)?tvcf\.co\.kr/play/", re.I)


def expand_tvcf(url):
    """TVCF 광고 페이지 → 로그인 없이 플레이어가 재생하는 스트림(720p) 주소."""
    req = urllib.request.Request(url, headers={"User-Agent": BROWSER_UA})
    with urllib.request.urlopen(req, timeout=15) as r:
        h = r.read().decode("utf-8", "replace")
    streams = sorted(set(s.replace("\\/", "/") for s in re.findall(
        r"https?:(?:\\/|/)+wowza\.tvcf\.co\.kr[^\"\s]*?playlist\.m3u8", h)))
    if not streams:
        return None
    best = next((s for s in streams if "_720p.mp4/" in s), None) or next((s for s in streams if not re.search(r"_i\.mp4/", s)), streams[0])
    t = re.search(r'og:title"\s+content="([^"]*)', h)
    title = re.sub(r"\s*\|\s*TVCF\s*$", "", t[1]).strip() if t else "TVCF video"
    code = re.search(r"/(A\w+?)(?:_720p|_i)?\.mp4/", best)
    img = re.search(r"https?://[\w.]+tvcf\.co\.kr/[^\"\s]*?" + re.escape(code[1]) + r"\.jpg", h) if code else None
    return {"t": title, "img": img[0] if img else "", "site": "TVCF", "v": [[best, title]]}


def tidy_info(info, url, name=""):
    """Behance 자체 영상(Adobe 플레이어)·일반 임베드는 제목/ID가 지저분하므로 정리."""
    if "wowza.tvcf.co.kr" in url:
        code = re.search(r"/(A\w+?)(?:_720p|_i)?\.mp4/", url)
        info["extractor_key"] = "TVCF"
        info["title"] = name or "TVCF video"
        if code:
            info["id"] = code[1]
        return info
    if re.match(r"^https://[\w-]+\.pinimg\.com/", url):
        info["extractor_key"] = "Pinterest"
        info["title"] = name or "Pinterest video"
        return info
    m = re.search(r"adobe\.io/v1/player/ccv/([\w-]+)", url)
    if m:
        info["id"] = m[1]
        info["title"] = name or "Behance video"
        info["extractor_key"] = "Behance"
    elif name and info.get("extractor_key") in ("Generic", "HTML5MediaEmbed"):
        info["title"] = name
    return info


# ── 썸네일 ─────────────────────────────────────────────
# 후보 이미지 주소를 차례로 시도 → 전부 실패하면 영상(받은 파일 또는 스트림)에서 한 장면 캡처
NOWIN = getattr(subprocess, "CREATE_NO_WINDOW", 0)
BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")


def is_image(b):
    return (b[:3] == b"\xff\xd8\xff" or b[:8] == b"\x89PNG\r\n\x1a\n" or b[:4] == b"GIF8"
            or (b[:4] == b"RIFF" and b[8:12] == b"WEBP") or b[4:12] in (b"ftypavif", b"ftypavis"))


def register_thumb(info):
    """영상 정보에서 썸네일 후보를 모아 등록하고 키를 돌려줌."""
    cands = []
    if info.get("thumbnail"):
        cands.append(info["thumbnail"])
    # yt-dlp는 선호도 낮은 것 → 높은 것 순으로 정렬해 둠. 좋은 것부터 시도
    for t in reversed(info.get("thumbnails") or []):
        u = t.get("url")
        if u and u not in cands:
            cands.append(u)
    # 캡처용 스트림: 영상이 있는 포맷 중 가장 작은 것 (빠름)
    stream = None
    vids = [f for f in info.get("formats") or [] if f.get("url") and f.get("vcodec") not in (None, "none")
            and (f.get("protocol") or "").split("+")[0] in ("https", "http", "m3u8", "m3u8_native")]
    if vids:
        f = min(vids, key=lambda f: f.get("height") or 9999)
        stream = (f["url"], f.get("http_headers") or {})
    key = uuid.uuid4().hex[:12]
    with LOCK:
        if len(THUMBS) > 300:
            for k in list(THUMBS)[:100]:
                THUMBS.pop(k, None)
        THUMBS[key] = {"cands": cands[:10], "referer": info.get("webpage_url") or "", "stream": stream,
                       "file": None, "data": None, "lock": threading.Lock()}
    return key


def fetch_image(url, referer):
    headers = {"User-Agent": BROWSER_UA, "Accept": "image/avif,image/webp,image/*,*/*;q=0.8"}
    if referer:
        headers["Referer"] = referer
    for h in (headers, {"User-Agent": BROWSER_UA}):  # Referer 때문에 막히는 경우 대비해 한 번 더
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=8) as r:
                b = r.read(8_000_000)
            if is_image(b):
                return b
        except Exception:
            pass
    return None


def grab_frame(src, headers=None):
    """ffmpeg로 영상에서 한 장면을 JPEG로 캡처."""
    best = None
    for ss in ("3", "1", "0"):  # 영상 맨 앞은 검은 화면인 경우가 많아 3초 지점부터
        cmd = [FFMPEG, "-loglevel", "error", "-y"]
        if headers:
            cmd += ["-headers", "".join(f"{k}: {v}\r\n" for k, v in headers.items())]
        cmd += ["-ss", ss, "-i", src, "-frames:v", "1", "-vf", "scale='min(960,iw)':-2", "-f", "image2pipe", "-vcodec", "mjpeg", "-"]
        try:
            r = subprocess.run(cmd, capture_output=True, timeout=25, creationflags=NOWIN)
            if r.returncode == 0 and is_image(r.stdout):
                if len(r.stdout) > 3000:  # 너무 작으면 거의 단색(검은 화면) → 다음 지점 시도
                    return r.stdout
                best = best or r.stdout
        except Exception:
            pass
    return best


def get_thumb(key):
    t = THUMBS.get(key)
    if not t:
        return None
    with t["lock"]:
        if t["data"]:
            return t["data"]
        data = None
        for u in t["cands"]:
            if (data := fetch_image(u, t["referer"])):
                break
        if not data and t["file"] and os.path.exists(t["file"]):
            data = grab_frame(t["file"])
        if not data and t["stream"] and not t.get("stream_failed"):
            data = grab_frame(*t["stream"])
            t["stream_failed"] = not data
        t["data"] = data
        return data


def image_type(b):
    if b[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if b[:4] == b"GIF8":
        return "image/gif"
    if b[:4] == b"RIFF":
        return "image/webp"
    return "image/avif"


def get_info(url):
    with yt_dlp.YoutubeDL({**base_opts(), "noplaylist": True}) as ydl:
        info = tidy_info(ydl.extract_info(fix_url(url), download=False), url)
    sizes = {}
    for f in info.get("formats") or []:
        h = f.get("height")
        if h and f.get("vcodec") not in (None, "none"):
            sizes[h] = max(sizes.get(h, 0), f.get("width") or 0)
    heights = [[h, sizes[h]] for h in sorted(sizes, reverse=True)]
    return {
        "title": info.get("title"),
        "thumb": "/thumb/" + register_thumb(info),
        "duration": info.get("duration"),
        "uploader": info.get("uploader") or info.get("channel"),
        "site": info.get("extractor_key"),
        "heights": heights,
    }


def update(job_id, **kw):
    with LOCK:
        JOBS[job_id].update(kw)


def to_h264(path, job_id):
    """프리미어 호환용 H.264 변환. NVIDIA 인코더 우선, 실패하면 CPU."""
    src = Path(path)
    out = src.with_name(src.stem + "_h264.mp4")
    update(job_id, status="converting", phase="Converting to H.264")
    # 그래픽카드 인코더 먼저(윈도우: NVIDIA, 맥: VideoToolbox), 안 되면 CPU
    gpu = ["h264_videotoolbox", "-q:v", "70"] if IS_MAC else ["h264_nvenc", "-preset", "p5", "-cq", "19"]
    for vcodec in (gpu, ["libx264", "-preset", "medium", "-crf", "18"]):
        cmd = [FFMPEG, "-y", "-loglevel", "error", "-i", str(src), "-c:v", *vcodec,
               "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "320k", str(out)]
        r = subprocess.run(cmd, capture_output=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if r.returncode == 0:
            src.unlink(missing_ok=True)
            return str(out)
    raise RuntimeError("H.264 conversion failed")


def run_job(job_id, url, quality, h264):
    def hook(d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            pct = (d.get("downloaded_bytes", 0) / total * 100) if total else 0
            info = d.get("info_dict") or {}
            kind = "Audio" if info.get("vcodec") == "none" else "Video"
            update(job_id, status="downloading", percent=round(pct, 1), phase=kind,
                   speed=ANSI.sub("", d.get("_speed_str", "")).strip(), eta=ANSI.sub("", d.get("_eta_str", "")).strip())
        elif d["status"] == "finished":
            update(job_id, percent=100, phase="Merging")

    out_dir = SAVE_DIR if JOBS[job_id].get("owner", "127.0.0.1") in LOCAL_IPS else TEAM_DIR / job_id
    opts = {**base_opts(), "noplaylist": True, "progress_hooks": [hook],
            "outtmpl": str(out_dir / "%(title).150B [%(id)s].%(ext)s"),
            "windowsfilenames": True}
    if quality == "audio":
        opts["format"] = "ba/b"
        opts["postprocessors"] = [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "320"}]
    else:
        h = int(quality) if quality.isdigit() else 99999
        opts["format"] = f"bv*[height<={h}]+ba/b[height<={h}]/bv*+ba/b"
        opts["merge_output_format"] = "mp4"

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            update(job_id, phase="Fetching info")
            info = tidy_info(ydl.extract_info(fix_url(url), download=False), url, JOBS[job_id].get("name", ""))
            thumb = JOBS[job_id].get("thumb") or "/thumb/" + register_thumb(info)
            update(job_id, title=info.get("title") or url, thumb=thumb, site=info.get("extractor_key") or "")
            info = ydl.process_ie_result(info, download=True)
            path = (info.get("requested_downloads") or [{}])[0].get("filepath") or ydl.prepare_filename(info)
        if quality != "audio" and h264:
            path = to_h264(path, job_id)
        # 썸네일을 못 구했으면 받은 파일에서 캡처할 수 있게 경로 등록
        t = THUMBS.get(thumb.rsplit("/", 1)[-1])
        if t:
            t["file"] = path
        update(job_id, status="done", percent=100, phase="Done", filename=os.path.basename(path), path=path)
    except Exception as e:
        update(job_id, status="error", phase="Failed", error=friendly_error(e))


def start_job(url, quality, h264, label="", title="", thumb="", name="", owner=""):
    job_id = uuid.uuid4().hex[:8]
    if not re.fullmatch(r"/thumb/[0-9a-f]{12}", thumb or ""):
        thumb = ""
    with LOCK:
        JOBS[job_id] = {"id": job_id, "owner": owner, "url": url, "title": name or title or url, "name": name, "thumb": thumb, "site": "",
                        "h264": h264, "quality": quality, "label": label, "status": "queued",
                        "percent": 0, "phase": "Queued", "speed": "", "eta": "", "filename": "", "error": ""}
    threading.Thread(target=run_job, args=(job_id, url, quality, h264), daemon=True).start()
    return job_id


def open_path(p, select=False):
    if IS_MAC:   # 맥: Finder
        subprocess.Popen(["open", "-R", p] if select and os.path.exists(p) else ["open", p])
    elif select and os.path.exists(p):
        subprocess.Popen(["explorer", "/select,", os.path.normpath(p)])
    else:
        os.startfile(p)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send_json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_thumb(self):
        """썸네일을 서버가 대신 구해서 전달 (인스타 등은 다른 사이트에서 직접 표시를 막음)."""
        if self.headers.get("Sec-Fetch-Site", "same-origin") not in ("same-origin", "none"):
            return self.send_error(403)
        data = get_thumb(urlparse(self.path).path.rsplit("/", 1)[-1])
        if not data:
            self.send_response(404)
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", image_type(data))
        self.send_header("Cache-Control", "max-age=86400")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    # ── 누가 접속했는지 / 들어와도 되는지 ──────────────────────
    @property
    def local(self):
        """이 PC에서 접속(127.0.0.1)."""
        return self.client_address[0] in ("127.0.0.1", "::1")

    @property
    def owner(self):
        return self.client_address[0]

    def host_ok(self):
        """주소창이 IP 주소나 localhost일 때만 응답(다른 사이트가 이 서버인 척하는 공격 차단)."""
        return bool(re.fullmatch(rf"(\d{{1,3}}(\.\d{{1,3}}){{3}}|localhost|\[::1\]):{PORT}", self.headers.get("Host", "")))

    def has_key(self):
        if self.local:
            return True
        if f"key={KEY}" in (urlparse(self.path).query or "").split("&"):   # 안내 페이지의 바로 받기 링크(…?key=)
            return True
        for part in (self.headers.get("Cookie") or "").split(";"):
            k, _, v = part.strip().partition("=")
            if k == "vd_key" and v == KEY:
                return True
        return False

    def deny(self):
        body = ("<!doctype html><meta charset=utf-8><title>Video Downloader</title>"
                "<body style='font-family:sans-serif;background:#e8e8e6;display:grid;place-items:center;height:90vh'>"
                "<div><h2>No access</h2><p>Open the team link (the one with <code>?key=</code>) once.</p></div>").encode()
        self.send_response(403)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, job_id):
        """받은 파일을 접속한 사람의 컴퓨터로 내려보냄(팀원용 Save 버튼)."""
        job = JOBS.get(job_id)
        if not job or job.get("status") != "done" or job.get("owner") != self.owner:
            return self.send_error(404)
        p = Path(job.get("path") or "")
        if not p.is_file():
            return self.send_error(404)
        from urllib.parse import quote
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(p.stat().st_size))
        self.send_header("Content-Disposition", f"attachment; filename=\"video{p.suffix}\"; filename*=UTF-8''{quote(p.name)}")
        self.end_headers()
        try:
            with open(p, "rb") as f:
                shutil.copyfileobj(f, self.wfile, 1024 * 1024)
            self.wfile.flush()
        except OSError:
            return   # 팀원이 저장을 취소/중단 → 파일은 남겨두고 다시 받을 수 있게
        if TEAM_DIR in p.parents:   # 팀원 컴퓨터로 다 넘어갔으면 이 PC에서는 삭제
            shutil.rmtree(p.parent, ignore_errors=True)
            update(job_id, delivered=True)

    def send_extension(self):
        """Behance 확장 프로그램 zip. 접속한 주소(예: 192.168.x.x)에서도 동작하도록 manifest를 맞춰서 줌."""
        import io
        import zipfile
        src = BASE_DIR / "behance-extension"
        host = self.headers.get("Host", "").rsplit(":", 1)[0]
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            for f in ("background.js", "content.js"):
                z.write(src / f, f"behance-extension/{f}")
            m = json.loads((src / "manifest.json").read_text(encoding="utf-8"))
            matches = m["content_scripts"][0]["matches"]
            if f"http://{host}/*" not in matches:
                matches.append(f"http://{host}/*")
            z.writestr("behance-extension/manifest.json", json.dumps(m, indent=2, ensure_ascii=False))
        data = buf.getvalue()
        self.send_response(200)
        self.send_header("Content-Type", "application/zip")
        self.send_header("Content-Disposition", 'attachment; filename="behance-extension.zip"')
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if not self.host_ok():
            return self.send_error(403)
        u = urlparse(self.path)
        if not self.local and f"key={KEY}" in (u.query or "").split("&"):
            # 키가 붙은 링크(팀 링크·사용법·확장 받기)로 들어옴 → 키를 쿠키로 저장하고 주소창에서 키를 지움
            self.send_response(302)
            self.send_header("Set-Cookie", f"vd_key={KEY}; Path=/; Max-Age=31536000; HttpOnly; SameSite=Lax")
            self.send_header("Location", u.path or "/")
            self.end_headers()
            return
        if not self.has_key():
            return self.deny()
        if u.path.startswith("/file/"):
            return self.send_file(u.path[6:])
        if u.path == "/extension.zip":
            return self.send_extension()
        if u.path == "/guide" and not (BASE_DIR / "guide.html").exists():
            return self.send_error(404)
        if u.path in ("/", "/index.html", "/guide"):
            body = (BASE_DIR / ("guide.html" if u.path == "/guide" else "index.html")).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)
        elif u.path in ("/icon.png", "/icon-180.png"):
            body = (BASE_DIR / u.path.lstrip("/")).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Cache-Control", "max-age=86400")
            self.end_headers()
            self.wfile.write(body)
        elif self.path.startswith("/thumb/"):
            self.send_thumb()
        elif self.path == "/api/jobs":
            with LOCK:
                mine = [{k: v for k, v in j.items() if k not in ("path", "owner")}
                        for j in JOBS.values() if j.get("owner") == self.owner][::-1]
            team = f"http://{lan_ip()}:{PORT}/?key={KEY}" if (self.local and TEAM) else ""
            self.send_json({"jobs": mine, "saveDir": str(SAVE_DIR) if self.local else "", "local": self.local,
                            "team": team, "guide": guide_url()})
        else:
            self.send_error(404)

    def do_POST(self):
        # 다른 사이트에서 이 로컬 서버를 호출하지 못하게 막음
        origin = self.headers.get("Origin")
        if not self.host_ok() or (origin and origin != f"http://{self.headers.get('Host')}"):
            return self.send_json({"error": "forbidden"}, 403)
        if not self.has_key():
            return self.send_json({"error": "No access. Open the team link once."}, 403)
        if self.path in ("/api/quit", "/api/browser") and not self.local:
            return self.send_json({"error": "forbidden"}, 403)
        length = int(self.headers.get("Content-Length") or 0)
        data = json.loads(self.rfile.read(length) or b"{}")
        try:
            if self.path == "/api/info":
                self.send_json(get_info(data["url"].strip()))
            elif self.path == "/api/expand":
                u = str(data.get("url", "")).strip()
                self.send_json((expand_tvcf(u) if TVCF_RE.match(u) else expand_pinterest(u)) or {"v": []})
            elif self.path == "/api/download":
                urls = [u.strip() for u in data.get("urls", []) if u.strip()]
                one = len(urls) == 1
                names = data.get("names") if isinstance(data.get("names"), dict) else {}
                ids = [start_job(u, str(data.get("quality", "best")), bool(data.get("h264")), str(data.get("label", ""))[:40],
                                 str(data.get("title", ""))[:300] if one else "",
                                 str(data.get("thumb", "")) if one else "",
                                 str(names.get(u) or "")[:200], self.owner)
                       for u in urls]
                self.send_json({"ids": ids})
            elif self.path == "/api/open":
                if not self.local:   # 이 PC의 탐색기를 다른 사람이 열 수는 없음
                    return self.send_json({"error": "forbidden"}, 403)
                job = JOBS.get(data.get("id", ""))
                if job and job.get("path"):
                    open_path(job["path"], select=True)
                else:
                    open_path(str(SAVE_DIR))
                self.send_json({"ok": True})
            elif self.path == "/api/quit":
                with LOCK:
                    busy = any(j["status"] in ("queued", "downloading", "converting") for j in JOBS.values())
                if busy:
                    return self.send_json({"ok": False, "reason": "busy"})
                self.send_json({"ok": True})
                print("\n새 버전 다운로더가 실행되어 이 창은 종료됩니다. 창을 닫아도 됩니다.")
                threading.Thread(target=self.server.shutdown, daemon=True).start()
            elif self.path == "/api/browser":   # 앱 창에서 "크롬에서 열기"(Behance 확장은 크롬에서만 동작)
                webbrowser.open(f"http://{HOST}:{PORT}/")
                self.send_json({"ok": True})
            elif self.path == "/api/clear":
                with LOCK:
                    for k in [k for k, j in JOBS.items() if j["status"] in ("done", "error") and j.get("owner") == self.owner]:
                        del JOBS[k]
                self.send_json({"ok": True})
            else:
                self.send_error(404)
        except Exception as e:
            self.send_json({"error": friendly_error(e)}, 400)


class Server(ThreadingHTTPServer):
    # 윈도우는 기본 설정이면 같은 포트에 서버가 여러 개 뜰 수 있음 → 하나만 잡도록 독점 모드
    allow_reuse_address = False
    daemon_threads = True

    def server_bind(self):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def ask_old_to_quit():
    """이미 떠 있는 예전 다운로더에게 종료를 요청. 진행 중인 다운로드가 있으면 거절됨."""
    try:
        req = urllib.request.Request(f"http://{HOST}:{PORT}/api/quit", b"{}", {"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as r:
            return "ok" if json.load(r).get("ok") else "busy"
    except Exception:
        return "fail"


if __name__ == "__main__":
    server = None
    for attempt in range(2):
        try:
            server = Server((BIND, PORT), Handler)
            break
        except OSError:
            res = ask_old_to_quit() if attempt == 0 else "fail"
            if res == "ok":
                print("예전 다운로더를 끄고 새 버전으로 교체합니다...")
                time.sleep(1.5)
                continue
            if res == "busy":
                print("다른 다운로더 창에서 다운로드가 진행 중이라 그 창을 그대로 사용합니다.")
                print("다운로드가 끝난 뒤 다시 실행하면 새 버전으로 교체됩니다.")
                webbrowser.open(f"http://{HOST}:{PORT}")
            else:
                print(f"포트 {PORT}을(를) 다른 프로그램이 쓰고 있습니다.")
                print("열려 있는 다운로더 창을 모두 닫고 다시 실행하세요.")
            sys.exit(1)
    clean_team_dir(0)   # 지난번에 남은 팀원 임시 파일 정리
    threading.Thread(target=_cleaner, daemon=True).start()
    print(f"영상 다운로더 실행 중: http://{HOST}:{PORT}")
    print(f"저장 위치: {SAVE_DIR}")
    if TEAM:
        print()
        print("── 팀원 공유 링크 (같은 사무실 네트워크에서만) ──")
        print(f"   http://{lan_ip()}:{PORT}/?key={KEY}")
        print("   이 링크를 팀원에게 보내주세요. 한 번 열면 그 브라우저는 계속 접속됩니다.")
        print()
    print("이 창을 닫으면 다운로더가 종료됩니다.")
    if "--no-browser" not in sys.argv:
        webbrowser.open(f"http://{HOST}:{PORT}")
    server.serve_forever()
