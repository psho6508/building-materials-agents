"""건축자재 유통 AI 멀티 에이전트 시스템 - 진입점.

사용법:
  # 일일 전략 브리핑 (전체 파이프라인)
  python main.py

  # 개별 에이전트 실행
  python main.py --agent bid_monitor
  python main.py --agent price_tracker
  python main.py --agent site_manager_crm
  python main.py --agent fixman_synergy
  python main.py --agent content_strategy

  # 에이전트 목록 확인
  python main.py --list
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Windows cp949 인코딩 문제 방지
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Claude Code 중첩 세션 방지 (SDK가 CLI를 서브프로세스로 실행할 때 필요)
os.environ.pop("CLAUDECODE", None)

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).parent))

# SDK monkey-patch 적용
from sdk_patch import apply_sdk_patches
apply_sdk_patches()

import anyio

from orchestrator import DailyStrategyOrchestrator, run_single_agent


AGENT_DESCRIPTIONS = {
    "market_scan": "시장 스캔 - 서울/경기 착공·입찰 감시 (4대 자재 카테고리)",
    "bid_monitor": "입찰/착공 감시 - 나라장터·세움터 공고 모니터링",
    "price_strategy": "시세 전략 - 4대 카테고리 시세 분석·마진 잠식·DO/HOLD/SKIP 판단",
    "price_tracker": "시세 추적 - 철강·시멘트·배관자재 시세 분석",
    "site_manager_crm": "소장 CRM - 563명 실데이터 기반 착공 매칭·기존고객/신규개척 판단",
    "fixman_synergy": "픽스맨 연동 - 점검 데이터 기반 패키지 제안",
    "content_strategy": "콘텐츠 전략 - 건자재TV 매출 연결 기획",
}


def check_prerequisites():
    """실행 전제조건 확인 (Claude Code CLI 설치 여부)."""
    import shutil
    if not shutil.which("claude"):
        print("⚠️  Claude Code CLI가 설치되지 않았거나 PATH에 없습니다.")
        print("   claude-code-sdk는 Claude Code CLI를 통해 동작합니다.")
        print("   설치: npm install -g @anthropic-ai/claude-code")
        sys.exit(1)


def list_agents():
    """사용 가능한 에이전트 목록 출력."""
    print("\n📋 사용 가능한 에이전트:")
    print("─" * 50)
    for name, desc in AGENT_DESCRIPTIONS.items():
        print(f"  {name:20s} │ {desc}")
    print("─" * 50)
    print(f"\n사용법: python main.py --agent <에이전트명>")


async def run_daily_briefing():
    """일일 전략 브리핑 실행."""
    orchestrator = DailyStrategyOrchestrator()
    briefing = await orchestrator.run()
    print("\n" + briefing)


async def run_agent(agent_name: str):
    """개별 에이전트 실행."""
    result = await run_single_agent(agent_name)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="건축자재 유통 AI 멀티 에이전트 시스템",
    )
    parser.add_argument(
        "--agent",
        type=str,
        choices=list(AGENT_DESCRIPTIONS.keys()),
        help="실행할 개별 에이전트 이름",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="사용 가능한 에이전트 목록 표시",
    )

    args = parser.parse_args()

    if args.list:
        list_agents()
        return

    check_prerequisites()

    if args.agent:
        print(f"\n🔧 개별 에이전트 실행: {args.agent}")
        print(f"   {AGENT_DESCRIPTIONS[args.agent]}")
        print()
        anyio.run(run_agent, args.agent)
    else:
        print("\n" + "═" * 50)
        print("🏗️  건축자재 유통 AI 멀티 에이전트 시스템")
        print("═" * 50)
        print("일일 전략 브리핑을 생성합니다...\n")
        anyio.run(run_daily_briefing)


if __name__ == "__main__":
    main()
