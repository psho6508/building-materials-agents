# 백원철물건재 키워드 분석 팀

컴퓨터가 꺼져 있어도 GitHub Actions가 하루 4번 실시간 트렌드를 수집해 백원철물건재와
연결되는 주제를 골라 텔레그램으로 보내고, 버튼으로 승인하면 블로그 글/영상 대본 초안을
만들어 저장소에 커밋합니다.

## 동작 흐름

1. **키워드 수집** (`collect_and_notify.py`, 하루 4회: KST 07/12/17/21시)
   - 네이트 실시간 이슈 키워드 (10개)
   - 줌 AI 이슈트렌드 (5개)
   - 구글 트렌드 한국 실시간 급상승 검색어 (10개, 다음 실시간 트렌드 대체 — 다음은
     공식 실시간 검색어 서비스를 종료했습니다)
   - 네이버 뉴스 랭킹 언론사별 1위 기사 (20개, 네이버 클립 대체 — 클립에는 공개된
     트렌드 API가 없습니다)
   - 수집된 전체 목록을 소스별로 텔레그램에 발송 (직전 회차에 없던 키워드는
     `🆕새로 진입` 표시)
   - Claude가 백원철물건재 고객의 실제 생활 상황(수전 고장, 전등 깜박임, 누수, 동파,
     철물점 이용 등)과 자연스럽게 연결되는 주제만 엄격하게 선별 — 사고/재난, 정치,
     연예인 이름이 포함된 키워드는 연결고리가 있어 보여도 항상 제외
   - 회차당 최대 2건까지만 후보 카드로 발송 (📝 글 발행 / 🎬 숏폼 제작 / 🔀 둘 다 /
     ❌ 넘김 버튼). 적합한 주제가 없으면 후보 카드는 보내지 않습니다.
   - 관련성 필터를 통과한 키워드는 승인 여부와 무관하게 `keyword_storage/{YYYY-MM-DD}.json`에
     일별로 누적 저장됩니다 (하루 4회 수집분이 같은 날짜 파일에 쌓임).
2. **승인 처리** (`check_approvals.py`, 10분 간격 폴링) — 버튼 클릭을 감지해 상태를
   `pending → done/rejected/error`로 바꾸므로 같은 버튼을 여러 번 눌러도 중복 처리되지 않음
   - **📝 글 발행**: 기존 발행 글(n8n) 스타일을 그대로 복제해 블로그 원고를 생성하고,
     구글 드라이브 `집수리 컨텐츠 원고(블로그, 티스토리)` 폴더에 구글 문서로 저장 →
     저장 완료되면 텔레그램으로 링크 회신. 사진/영상은 `집수리 현장 사진 및 영상`
     폴더에서 직접 골라 넣고, 티스토리에는 사람이 수동으로 붙여넣기 발행 (공식
     글쓰기 API가 폐지되어 자동 발행 불가)
   - **🎬 숏폼 제작**: 30~60초 대본을 생성해 `drafts/video/`에 커밋하고 GitHub 링크를
     텔레그램으로 회신. 실제 영상 제작(OpenMontage)은 에이전트가 단계별로 사람 승인을
     받으며 진행하는 구조라 무인 자동화가 불가능 — 대본 확인 후 별도로 제작/업로드
   - **🔀 둘 다**: 위 두 가지를 순서대로 실행하고 결과를 한 메시지로 회신

## 최초 설정 (1회)

GitHub 저장소 Settings → Secrets and variables → Actions 에 아래 4개를 등록하세요.
토큰은 민감정보이므로 직접 등록해주세요 (아래 명령을 터미널에서 실행하거나 웹 UI 사용):

```bash
gh secret set ANTHROPIC_API_KEY
gh secret set TELEGRAM_BOT_TOKEN
gh secret set TELEGRAM_CHAT_ID
gh secret set GOOGLE_SERVICE_ACCOUNT_JSON
```

`GOOGLE_SERVICE_ACCOUNT_JSON`은 bank-ledger 프로젝트에서 쓰던 서비스 계정을 그대로
재사용할 수 있습니다 (같은 JSON 키 내용을 이 저장소 시크릿으로도 등록). 단, 그
서비스 계정 이메일(JSON의 `client_email` 값)을 구글 드라이브의
`집수리 컨텐츠 원고(블로그, 티스토리)` 폴더에 **편집자로 공유**해줘야 저장이 됩니다.
해당 구글 프로젝트에서 Drive API가 활성화돼 있어야 합니다.

설정 후 `baekwon-keyword-collect.yml`을 Actions 탭에서 수동 실행(workflow_dispatch)해
텔레그램 카드가 오는지 확인하세요. 이후 자동 스케줄대로 동작합니다.

## 로컬 테스트

```bash
cd baekwon_keyword
pip install -r requirements.txt
cp .env.example .env  # 값 채우기
python -c "import os,dotenv" 2>/dev/null || pip install python-dotenv
python collect_and_notify.py
```

## 파일 구조

- `sources.py` — 4개 소스 스크레이퍼
- `relevance.py` — Claude 기반 관련성 필터링
- `content_draft.py` — 블로그 원고/영상 대본 생성 (블로그는 n8n 발행 글 예시를 few-shot으로 사용)
- `gdrive.py` — 블로그 원고를 구글 드라이브에 구글 문서로 저장
- `telegram_api.py` — 텔레그램 발송/수신
- `state.py` — 상태 저장(`state/pending_candidates.json`, `state/telegram_offset.json`)
- `keyword_storage.py` — 관련 키워드 일별 누적 저장 (`keyword_storage/{날짜}.json`)
- `drafts/` — 승인된 초안 (blog/, video/)
