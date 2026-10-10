"""백원철물건재 키워드 분석 봇 설정값."""

import os

# 브랜드 컨텍스트 (관련성 판단 + 콘텐츠 생성에 사용)
BRAND_NAME = "백원철물건재"
BRAND_CONTEXT = (
    "백원철물건재는 철물, 공구, 집수리 자재, 건축자재를 취급하는 유통업체입니다. "
    "타겟 고객은 (1) B2B 시공업체/현장소장, (2) B2C DIY 소비자, (3) 건설사 구매담당자입니다. "
    "관심 카테고리: 철물, 공구, 하드웨어, 집수리, 누수/방수, 전기/배관 자재, 페인트/도장, "
    "단열재, 철강재, 인테리어 자재, 셀프 인테리어, 장마/한파 등 계절 집수리 이슈, "
    "건축 현장 안전/자재 가격 동향, 공구 트렌드."
)

# Anthropic API
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")

# Telegram
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# 수집 소스별 목표 개수
SOURCE_LIMITS = {
    "nate_issue": 10,       # 네이트 실시간 이슈 키워드
    "zum_ai_trend": 5,      # 줌 AI 이슈트렌드
    "google_trends_kr": 10, # 구글 트렌드 한국 실시간 급상승 검색어 (다음 대체)
    "naver_news_rank": 20,  # 네이버 뉴스 랭킹 언론사별 1위 기사 (네이버 클립 대체)
}

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}
REQUEST_TIMEOUT = 15

# 경로
import pathlib
ROOT_DIR = pathlib.Path(__file__).parent
STATE_DIR = ROOT_DIR / "state"
DRAFTS_DIR = ROOT_DIR / "drafts"
PENDING_PATH = STATE_DIR / "pending_candidates.json"
OFFSET_PATH = STATE_DIR / "telegram_offset.json"
SEEN_PATH = STATE_DIR / "seen_keywords.json"

# 후보 카드 최대 발송 개수 (수집 1회당, "시간당 최대 2건" 기준)
MAX_CANDIDATES_PER_RUN = 2

# GitHub 저장소 (초안 URL 생성용)
GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "psho6508/building-materials-agents")
GITHUB_BRANCH = os.environ.get("GITHUB_BRANCH", "master")
