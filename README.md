<p align="center"><img src="icon.png" width="88" alt=""></p>

<h1 align="center">Video Downloader</h1>

<p align="center">영상 링크를 붙여넣으면 내 컴퓨터 <b>다운로드 폴더</b>로 바로 저장됩니다.<br>
YouTube · Vimeo · Instagram · TikTok · X · Pinterest · TVCF · Behance</p>

---

## 설치 (처음 한 번만)

- 내 컴퓨터 안에서만 돌아가서 **회사·집 어디서든, 다른 사람 PC가 꺼져 있어도** 쓸 수 있어요.
- 관리자 비밀번호는 필요 없어요. 처음 설치는 인터넷 속도에 따라 **1~3분** 걸립니다.
- 설치 중에는 터미널 창을 **닫지 마세요**. `설치 완료!`가 나오면 닫아도 됩니다.

### 🍎 맥

**1. 터미널 열기** (둘 중 편한 방법으로)

- **방법 A — Spotlight로 열기**
  1. 키보드에서 `⌘ Command` + `Space`를 같이 누릅니다. (화면 가운데 검색창이 뜸)
  2. `터미널` (또는 `terminal`) 이라고 입력합니다.
  3. **터미널** 앱이 선택된 상태에서 `Enter`
- **방법 B — Finder로 열기**
  Finder → **응용 프로그램** → **유틸리티** 폴더 → **터미널** 더블클릭

흰색(또는 검은색) 창이 열리고 `내이름@맥이름 ~ %` 같은 글자가 보이면 성공입니다.

**2. 아래 한 줄을 복사 → 터미널에 붙여넣기(`⌘ V`) → `Enter`**

```bash
curl -fsSL https://raw.githubusercontent.com/pakjy1339/video-downloader/main/install.sh | bash
```

**3. 진행 화면**
빨간 `▶ 1/5` ~ `▶ 5/5` 줄이 차례로 나옵니다. `3/5`에서 1~3분 멈춰 있는 건 정상이에요.

**4. 완료 확인**
초록색 `설치 완료!`가 나오고 브라우저에 다운로더(빨간 아이콘 화면)가 열리면 끝. 북마크(`⌘ D`) 해두세요.

- 다시 열 때: Spotlight(`⌘ Space`)에서 **Video Downloader** 검색 → `Enter`
  (앱 위치: Finder → 홈 폴더 → **응용 프로그램** 안. Dock에 끌어다 두면 편해요)
- 맥을 켜고 로그인하면 자동으로 실행됩니다.
- 처음 영상을 받을 때 *"다운로드 폴더에 접근하려고 합니다"* 같은 창이 뜨면 **허용**을 누르세요.

### 🪟 윈도우

**1. PowerShell 열기** (둘 중 편한 방법으로)

- **방법 A — 검색으로 열기**
  1. 키보드의 `⊞ 윈도우 키`를 한 번 누릅니다. (또는 작업 표시줄의 🔍 검색 칸 클릭)
  2. `powershell` 이라고 입력합니다.
  3. 검색 결과 맨 위의 **Windows PowerShell**이 선택된 상태에서 `Enter`
- **방법 B — 시작 버튼으로 열기**
  1. 화면 아래 **시작 버튼(⊞)을 마우스 오른쪽 클릭**
  2. 메뉴에서 **터미널** 클릭 (윈도우 10은 **Windows PowerShell**)

검은색(또는 파란색) 창이 열리고 `PS C:\Users\내이름>` 같은 글자가 보이면 성공입니다.
**관리자 권한(관리자로 실행)은 필요 없어요.** 일반으로 열면 됩니다.

**2. 아래 한 줄을 복사 → 창에 붙여넣기(`Ctrl V` 또는 마우스 오른쪽 클릭) → `Enter`**

```powershell
powershell -ExecutionPolicy Bypass -c "irm https://raw.githubusercontent.com/pakjy1339/video-downloader/main/install.ps1 | iex"
```

**3. 진행 화면**
빨간 `> 1/5` ~ `> 5/5` 줄이 차례로 나옵니다. `3/5`에서 1~3분 멈춰 있는 건 정상이에요.

**4. 완료 확인**
초록색 `설치 완료!`가 나오고 브라우저에 다운로더가 열리면 끝. 즐겨찾기(`Ctrl D`) 해두세요.

- 다시 열 때: 바탕화면의 **Video Downloader** 아이콘 (또는 시작 메뉴에서 검색)
- 아이콘 오른쪽 클릭 → **작업 표시줄에 고정**하면 편해요.
- 컴퓨터를 켜고 로그인하면 자동으로 실행됩니다.

> 다운로더 주소는 맥·윈도우 모두 **http://127.0.0.1:8765** 입니다. (내 컴퓨터 전용 주소라 다른 사람에게 보내도 열리지 않아요)

---

## 영상 받기

1. **링크 붙여넣기** — 입력칸에 붙여넣으면 영상 정보를 자동으로 불러와요. 여러 개는 `Shift + Enter`로 줄을 바꿔 넣으세요.
2. **화질 고르기** — `Best`는 가장 높은 화질, `MP3`는 소리만. 프리미어에서 쓸 거면 **Convert to H.264**를 켜세요.
3. **Download** — 끝나면 `다운로드/VideoDownloader` 폴더에 저장돼요. 오른쪽 위 **Downloads** 버튼으로 바로 열 수 있어요.

Behance·핀터레스트 링크는 그 안의 영상들이 자동으로 풀려 들어옵니다. (Behance는 아래 확장 프로그램 필요)

---

## Behance 확장 프로그램 (Behance 쓸 때만)

Behance 프로젝트 링크에서 영상만 골라 받으려면 크롬(또는 엣지)에 확장 프로그램을 한 번 설치해야 해요. **다운로더 설치를 먼저 끝낸 뒤** 진행하세요.

1. 다운로더가 켜진 상태에서 **[확장 프로그램 받기](http://127.0.0.1:8765/extension.zip)** 를 누릅니다. `behance-extension.zip`이 다운로드 폴더에 받아져요.
2. 압축을 풉니다.
   - 맥: zip 파일 더블클릭 → `behance-extension` 폴더가 생김
   - 윈도우: zip 파일 오른쪽 클릭 → **모두 압축 풀기** → **압축 풀기**
3. 풀린 폴더를 **문서** 폴더로 옮깁니다. (이 폴더를 지우면 확장 프로그램도 사라져요)
   - 안에 `manifest.json` 파일이 바로 보이는 폴더가 맞는 폴더예요. 폴더 안에 같은 이름 폴더가 한 겹 더 있으면 안쪽 폴더를 쓰세요.
4. 크롬 주소창에 `chrome://extensions` 입력 → `Enter` (엣지는 `edge://extensions`)
5. 오른쪽 위 **개발자 모드** 스위치 켜기 (엣지는 왼쪽 메뉴 아래)
6. **압축해제된 확장 프로그램을 로드합니다** 클릭 → 3번의 `behance-extension` 폴더 선택
7. 목록에 **Video Downloader – Behance**가 생기면 성공. 다운로더 탭을 **새로고침**하세요.
8. Behance 링크를 붙여넣어 영상 목록이 뜨면 완료!

> 크롬을 켤 때 "개발자 모드 확장 프로그램 사용 중지" 알림이 뜨면 **닫기**(X)를 누르면 됩니다. 사용 중지를 누르면 Behance가 안 돼요.

---

## 업데이트

**자동입니다.** 다운로더가 켜질 때마다(컴퓨터를 켜고 로그인할 때) 최신 버전과 최신 yt-dlp를 받아옵니다.
지금 바로 업데이트하려면 위 설치 명령을 한 번 더 실행하세요. (받아둔 영상은 그대로예요)

## 안 될 때

| 증상 | 해결 |
|---|---|
| 브라우저에 `연결할 수 없음`이 떠요 | 다운로더가 꺼진 상태예요. 맥: Spotlight에서 Video Downloader 실행 / 윈도우: 바탕화면 아이콘 실행. 10초쯤 뒤 새로고침. 그래도 안 되면 설치 명령을 다시 실행 |
| 설치 중 빨간 오류 글자가 나와요 | 창 전체를 캡처해서 담당자에게 보내주세요 |
| 회사 보안 프로그램이 설치를 막아요 | 화면을 캡처해서 IT 담당자에게 문의해 주세요 |
| `Private video` | 비공개 영상이라 받을 수 없어요 |
| `Vimeo refused this video` | 비공개이거나 주인이 막아둔 비메오 영상이에요 |
| Behance 링크를 넣으면 확장 프로그램이 필요하다고 떠요 | 위 **Behance 확장 프로그램** 설치 후 다운로더 탭 새로고침 |

## 제거

받은 영상은 그대로 남아요.

```bash
# 맥 (터미널)
curl -fsSL https://raw.githubusercontent.com/pakjy1339/video-downloader/main/uninstall.sh | bash
```

```powershell
# 윈도우 (PowerShell)
powershell -ExecutionPolicy Bypass -c "irm https://raw.githubusercontent.com/pakjy1339/video-downloader/main/uninstall.ps1 | iex"
```

Behance 확장 프로그램은 `chrome://extensions`에서 **삭제**를 누르세요.
