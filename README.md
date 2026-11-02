# 인생시 — 삶의 의미를 묻는 15일

안젤름 그륀 「목표를 가져라」를 2026-11-09 ~ 11-27 동안 하루 한 구절씩 함께 읽고 묵상을 기록하는 웹앱.
발표: 2026-12-06.

- **화면**: GitHub Pages (`index.html`, `days.js`, `config.js`)
- **저장**: Google Apps Script + Google 시트 (`apps-script/Code.gs`)
- 참여자는 로그인 없이 **이름 + 숫자 PIN 4자리**로 들어옵니다.
- 관리자 화면: 주소 뒤에 `#admin` 을 붙입니다.

## 1. Google 쪽 설정 (한 번만, 5분)

1. [sheets.new](https://sheets.new) 로 새 스프레드시트를 만들고 이름을 `인생시 묵상` 으로 바꿉니다.
2. 메뉴 **확장 프로그램 → Apps Script** 를 엽니다.
3. 편집기에 있는 내용을 모두 지우고 `apps-script/Code.gs` 의 내용을 붙여넣은 뒤 저장(💾)합니다.
4. 왼쪽 톱니 **프로젝트 설정 → 스크립트 속성 → 속성 추가**:
   - 속성 `ADMIN_KEY`, 값 = 관리자 비밀번호(원하는 문자열). 저장.
5. 오른쪽 위 **배포 → 새 배포**:
   - 유형 선택(톱니) → **웹 앱**
   - 설명: 아무거나
   - 다음 사용자 인증 정보로 실행: **나**
   - 액세스 권한이 있는 사용자: **모든 사용자** (중요)
   - **배포** → 권한 승인 창이 뜨면 본인 계정으로 승인 ("확인되지 않은 앱" 경고가 나오면 *고급 → 이동* 으로 진행)
6. 표시되는 **웹 앱 URL** (`https://script.google.com/macros/s/…/exec`)을 복사합니다.
7. 이 저장소의 `config.js` 를 열어 `window.API_URL = "여기에 붙여넣기";` 로 바꾸고 커밋합니다.

확인: 브라우저에서 웹 앱 URL을 직접 열면 `{"ok":true,"time":"…"}` 가 보여야 합니다.
첫 요청이 들어오면 시트에 `users`, `reflections` 탭이 자동으로 생깁니다.

> Code.gs 를 나중에 수정하면 **배포 → 배포 관리 → 연필 → 버전: 새 버전 → 배포** 를 해야 반영됩니다. URL은 그대로입니다.

## 2. GitHub Pages

저장소 **Settings → Pages → Source: Deploy from a branch → `main` / `(root)`** → Save.
몇 분 뒤 `https://<계정>.github.io/<저장소>/` 에서 열립니다.

## 데이터 (시트 `reflections`)

| 열 | 의미 |
|---|---|
| day | 1~19 또는 `final`(마무리 문장) |
| isPublic | 참여자가 공개를 선택했는지 |
| selected | 관리자가 발표용으로 선정했는지 |

시트는 관리자 모아보기와 동일한 데이터이므로, 발표 준비는 시트에서 직접 해도 됩니다.

## 테스트용 날짜 바꾸기

주소 뒤에 `?today=2026-11-15` 처럼 붙이면 그 날짜 기준으로 화면이 열립니다(개발 확인용).

## 구절·질문 수정

`days.js` 를 고치면 됩니다. 날짜(`startDate`, `finalOpen`, `finalClose`, `presentationDate`)도 여기서 바꿉니다.

## 배경음악
`audio/bgm.mp3` — "Warm Light" by David Fesliyan (FesliyanStudios.com). 앱은 이 파일을 음성 재생 중에만 낮은 음량으로 반복 재생합니다. 다른 곡으로 바꾸려면 이 파일만 교체하면 됩니다.

## 낭독 음성
- `audio/human/` — 모임 구성원 낭독(기본, 배경음악 포함 원본). 음량 정규화 후 문단 단위로 분할. 이 음성에서는 앱 배경음악이 꺼짐. 처리 절차: `docs/낭독대본.md` 참고.
- `audio/sunhi/`, `audio/injoon/` — AI 음성(예비). `tools/make_audio.py` 로 생성.
