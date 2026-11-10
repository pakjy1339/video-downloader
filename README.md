<p align="center"><img src="icon.png" width="88" alt=""></p>

<h1 align="center">Video Downloader</h1>

<p align="center">영상 링크를 붙여넣으면 내 컴퓨터 <b>다운로드 폴더</b>로 바로 저장됩니다.<br>
YouTube · Vimeo · Instagram · TikTok · X · Pinterest · TVCF · Behance</p>

---

## 설치 (한 번만)

내 컴퓨터 안에서만 돌아가서 **회사·집 어디서든** 쓸 수 있어요. 관리자 비밀번호는 필요 없고, 처음 설치는 1~3분 걸립니다.

### 🍎 맥

1. **터미널**을 엽니다. (`⌘ Space` → "터미널" 입력 → `Enter`)
2. 아래 한 줄을 복사해서 붙여넣고 `Enter`.

```bash
curl -fsSL https://raw.githubusercontent.com/pakjy1339/video-downloader/main/install.sh | bash
```

3. "설치 완료!"가 나오고 브라우저에 다운로더가 열리면 끝. 북마크(`⌘D`) 해두세요.

- **응용 프로그램** 폴더(Launchpad)에 빨간 아이콘의 **Video Downloader**가 생겨요. Dock으로 끌어다 두면 편해요.
- 맥을 켜면 자동으로 실행됩니다.

### 🪟 윈도우

1. **시작 버튼**을 오른쪽 클릭 → **터미널** (또는 Windows PowerShell)을 엽니다.
2. 아래 한 줄을 복사해서 붙여넣고 `Enter`.

```powershell
powershell -ExecutionPolicy Bypass -c "irm https://raw.githubusercontent.com/pakjy1339/video-downloader/main/install.ps1 | iex"
```

3. "설치 완료!"가 나오고 브라우저에 다운로더가 열리면 끝. 즐겨찾기(`Ctrl+D`) 해두세요.

- 바탕화면에 **Video Downloader** 아이콘이 생겨요. 오른쪽 클릭 → **작업 표시줄에 고정**하면 편해요.
- 컴퓨터를 켜면 자동으로 실행됩니다.

> 다운로더 주소는 맥·윈도우 모두 **http://127.0.0.1:8765** 입니다.

---

## 영상 받기

1. **링크 붙여넣기** — 입력칸에 붙여넣으면 영상 정보를 자동으로 불러와요. 여러 개는 `Shift + Enter`로 줄을 바꿔 넣으세요.
2. **화질 고르기** — `Best`는 가장 높은 화질, `MP3`는 소리만. 프리미어용이면 **Convert to H.264**를 켜세요.
3. **Download** — 끝나면 다운로드 폴더(`다운로드/VideoDownloader`)에 저장돼요. 오른쪽 위 **Downloads** 버튼으로 바로 열 수 있어요.

Behance·핀터레스트 링크는 그 안의 영상들이 자동으로 풀려 들어옵니다.

---

## Behance 확장 프로그램 (선택)

Behance 프로젝트 링크에서 영상만 골라 받으려면 크롬(또는 엣지) 확장 프로그램이 한 번 필요해요.

1. 다운로더를 연 상태에서 **[확장 프로그램 받기](http://127.0.0.1:8765/extension.zip)** 를 누릅니다.
2. 받은 `behance-extension.zip`의 압축을 풉니다.
   - 맥: 더블클릭
   - 윈도우: 오른쪽 클릭 → **모두 압축 풀기** (폴더가 한 겹 더 생기면, `manifest.json`이 보이는 안쪽 폴더가 맞아요)
3. 그 폴더를 **문서** 폴더로 옮깁니다. (지우면 확장 프로그램도 꺼져요)
4. 주소창에 `chrome://extensions` (엣지는 `edge://extensions`) → **개발자 모드** 켜기
5. **압축해제된 확장 프로그램을 로드합니다** → 문서 안의 `behance-extension` 폴더 선택
6. 다운로더를 새로고침하고 Behance 링크를 붙여넣어 영상 목록이 뜨면 완료!

---

## 업데이트

**자동입니다.** 다운로더가 켜질 때마다(컴퓨터를 켤 때) 최신 버전과 최신 yt-dlp를 받아옵니다.
바로 업데이트하고 싶으면 설치 명령을 한 번 더 실행하면 돼요.

## 안 될 때

| 증상 | 해결 |
|---|---|
| 브라우저에서 안 열려요 | 맥: Launchpad의 Video Downloader 실행 / 윈도우: 바탕화면 아이콘 실행. 그래도 안 되면 설치 명령을 다시 실행 |
| `Private video` | 비공개 영상이라 받을 수 없어요 |
| `Vimeo refused this video` | 비공개이거나 주인이 막아둔 비메오 영상이에요 |
| 회사 보안 프로그램이 막아요 | 설치·실행이 보안 프로그램에 막히면 담당자에게 문의해 주세요 |

## 제거

받은 영상은 그대로 남아요.

```bash
# 맥
curl -fsSL https://raw.githubusercontent.com/pakjy1339/video-downloader/main/uninstall.sh | bash
```

```powershell
# 윈도우
powershell -ExecutionPolicy Bypass -c "irm https://raw.githubusercontent.com/pakjy1339/video-downloader/main/uninstall.ps1 | iex"
```
