"""설정값 관리 모듈.

환경변수에서 API 키를 읽고, 에이전트 공통 설정을 제공한다.
"""

import os
from pathlib import Path

# 프로젝트 루트 디렉토리
PROJECT_ROOT = Path(__file__).parent

# 데이터 디렉토리
DATA_DIR = PROJECT_ROOT / "data"

# Anthropic API 키
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# Claude 모델 설정 (SDK는 CLI를 통해 실행하므로 CLI가 지원하는 모델 사용)
MODEL = "sonnet"

# 에이전트 공통 설정
MAX_TURNS = 10  # 에이전트 최대 턴 수
AGENT_TIMEOUT = 300  # 에이전트 실행 타임아웃 (초)
RATE_LIMIT_SLEEP = 10  # rate limit 방지 대기 (초)

# 브리핑 출력 디렉토리
OUTPUT_DIR = PROJECT_ROOT / "output"

# 건축 공정 단계별 필요 자재 매핑
CONSTRUCTION_PHASE_MATERIALS = {
    "터파기": ["토목용 자재", "가시설 자재"],
    "기초공사": ["철근", "시멘트", "레미콘", "거푸집"],
    "골조공사": ["철근", "시멘트", "레미콘", "거푸집", "철골"],
    "방수공사": ["방수시트", "방수도료", "실란트"],
    "배관공사": ["PVC파이프", "동파이프", "밸브류", "배관자재"],
    "전기공사": ["전선", "배선기구", "조명기구", "분전반"],
    "내장공사": ["석고보드", "타일", "도배지", "바닥재", "몰딩"],
    "외장공사": ["외장재", "단열재", "창호", "유리"],
    "설비공사": ["보일러", "에어컨배관", "소방자재", "위생도기"],
    "마감공사": ["도료", "실리콘", "코킹재", "하드웨어"],
}

# 자재 카테고리별 가격 변동 임계값 (%)
PRICE_ALERT_THRESHOLDS = {
    "급등": 5.0,
    "상승": 2.0,
    "안정": -2.0,  # 이 이상이면 안정
    "하락": -5.0,
}

# 수익성 기반 의사결정 임계값
MARGIN_THRESHOLDS = {
    "우선추진": 20.0,   # 마진율 20% 이상 → 적극 추진
    "조건부추진": 15.0, # 마진율 15~20% → 조건부 추진
    "재검토": 0.0,      # 마진율 15% 미만 → 재검토 필요
}

# 고객 연락 긴급도 기준 (일)
CONTACT_URGENCY_DAYS = {
    "즉시": 14,  # 마지막 연락 후 14일 이상 경과 → 즉시 연락
    "이번주": 7, # 마지막 연락 후 7일 이상 경과 → 이번 주 연락
}

# 객단가(AOV) 상승 목표 (%)
AOV_INCREASE_TARGET_PCT = 20.0

# 콘텐츠 제작 비용 (원)
CONTENT_PRODUCTION_COST = 500000

# ── 시장 스캔 에이전트 설정 ──

# 감시 대상 지역
MARKET_SCAN_REGION = ["서울특별시", "경기도"]

# 4대 핵심 자재 카테고리
MATERIAL_CATEGORIES = ["단열재", "철강재", "철물자재", "건축자재"]

# DO/HOLD/SKIP 마진 기준 (원)
DECISION_MARGIN_THRESHOLDS = {
    "DO_UNCONDITIONAL": 2_000_000,  # 200만원↑ → 무조건 DO
    "DO": 1_000_000,                # 100만원↑ + 서울/경기 + 납기 2주↑ → DO
    "HOLD_MIN": 500_000,            # 50~100만원 → HOLD
    "SKIP": 500_000,                # 50만원↓ → SKIP
}

# ── 시세 전략 에이전트 설정 ──

# 마진 잠식 기준 (%p) — DO/HOLD/SKIP 판단
MARGIN_EROSION_THRESHOLDS = {
    "DO": 3.0,        # 마진 잠식 3%p 이상 → 단가 인상 필요
    "HOLD_MIN": 1.0,  # 마진 잠식 1~3%p → 추이 관찰
    "SKIP": 1.0,      # 마진 잠식 1%p 미만 → 조치 불필요
}

# ── 소장 CRM 에이전트 설정 ──

# 소장 DB CSV 파일명
CRM_CSV_FILENAME = "건설회사_소장 데이터.csv"

# 등급별 우선순위 (낮을수록 높은 우선순위)
CRM_GRADE_PRIORITY = {
    "HOT": 1,
    "HIGH WARM": 2,
    "LOW WARM": 3,
    "COLD": 4,
    "COLD-L": 5,
    "COLD-D": 6,
}
