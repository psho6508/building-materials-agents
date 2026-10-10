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
   - 회차당 최대 2건까지만 후보 카드로 발송 (📝 블로그 발행 / 🎬 영상 제작 / ❌ 거절
     버튼). 적합한 주제가 없으면 후보 카드는 보내지 않습니다.
2. **승인 처리** (`check_approvals.py`, 10분 간격 폴링)
   - 버튼 클릭을 감지해 블로그 초안(2000~3000자, 네이버 SEO 구조) 또는 영상 대본
     (30~60초 숏폼)을 생성
   - `drafts/blog/` 또는 `drafts/video/`에 커밋하고, 완성된 GitHub 파일 링크를
     텔레그램으로 회신
   - ⚠️ 네이버에는 공식 글쓰기 API가, 유튜브 업로드에는 OAuth 인증이 필요해 **실제
     발행/업로드는 자동화하지 않습니다.** 초안을 확인하고 직접 올려주세요.

## 최초 설정 (1회)

GitHub 저장소 Settings → Secrets and variables → Actions 에 아래 3개를 등록하세요.
토큰은 민감정보이므로 직접 등록해주세요 (아래 명령을 터미널에서 실행하거나 웹 UI 사용):

```bash
gh secret set ANTHROPIC_API_KEY
gh secret set TELEGRAM_BOT_TOKEN
gh secret set TELEGRAM_CHAT_ID
```

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
- `content_draft.py` — 블로그/영상 대본 초안 생성
- `telegram_api.py` — 텔레그램 발송/수신
- `state.py` — 상태 저장(`state/pending_candidates.json`, `state/telegram_offset.json`)
- `drafts/` — 승인된 초안 (blog/, video/)
