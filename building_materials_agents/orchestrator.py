"""Daily Strategy Orchestrator.

5개 에이전트를 순차 실행하고, 결과를 종합하여 일일 전략 브리핑을 생성한다.
"""

import json
import sys
from datetime import date
from pathlib import Path

import anyio
from claude_code_sdk import query, ClaudeCodeOptions, AssistantMessage, TextBlock

from config import MAX_TURNS, MODEL, OUTPUT_DIR, AGENT_TIMEOUT, RATE_LIMIT_SLEEP
from agents import (
    BidMonitorAgent,
    ContentStrategyAgent,
    FixmanSynergyAgent,
    MarketScanAgent,
    PriceStrategyAgent,
    PriceTrackerAgent,
    SiteManagerCRMAgent,
)


ORCHESTRATOR_PROMPT = (
    "당신은 건축자재 유통업체의 일일 전략 총괄 디렉터입니다. "
    "5개 에이전트 결과를 종합하여 수익(profit) 중심 브리핑을 작성합니다. "
    "핵심 원칙: 매출이 아닌 수익(profit) 기준으로 모든 우선순위 결정. "
    "브리핑 5단 구조: "
    "(1) 오늘의 수익 대시보드 - 전체 파이프라인 매출/원가/수익/마진율 합산 테이블, "
    "(2) GO 리스트 - 모든 에이전트의 GO/YES/TODAY/PROPOSE-TODAY/PUBLISH-TODAY 항목을 수익 크기 내림차순 정렬, "
    "(3) 객단가 상승 기회 - 번들/크로스셀/업셀 통합 (기본주문 대비 추가매출 비율), "
    "(4) 리스크 경고 - 마진<15% 항목, 재고부족(inventory_qty<reorder_point), 연락공백>=14일, "
    "(5) 에이전트별 상세 - 기존 포맷 + 수익정보. "
    "금액은 만원 단위로 표시하세요."
)


class DailyStrategyOrchestrator:
    """일일 전략 오케스트레이터."""

    def __init__(self):
        self.agents = {
            "market_scan": MarketScanAgent(),
            "bid_monitor": BidMonitorAgent(),
            "price_strategy": PriceStrategyAgent(),
            "price_tracker": PriceTrackerAgent(),
            "site_manager_crm": SiteManagerCRMAgent(),
            "fixman_synergy": FixmanSynergyAgent(),
            "content_strategy": ContentStrategyAgent(),
        }

    async def run(self) -> str:
        """5개 에이전트를 순차 실행 후 결과 종합."""
        print("=" * 50)
        print("🚀 일일 전략 브리핑 생성을 시작합니다...")
        print("=" * 50)

        # Phase 1: 4개 에이전트 순차 실행 (rate limit 방지 10초 간격, 타임아웃 300초)
        phase1_agents = [
            "bid_monitor",
            "price_tracker",
            "site_manager_crm",
            "fixman_synergy",
        ]
        print(f"\n📡 Phase 1: {len(phase1_agents)}개 에이전트 순차 실행 중 ({RATE_LIMIT_SLEEP}초 간격, 타임아웃 {AGENT_TIMEOUT}초)...")
        results = {}

        for i, name in enumerate(phase1_agents):
            agent = self.agents[name]
            print(f"  ▶ [{i+1}/{len(phase1_agents)}] {agent.description} 에이전트 시작...")
            try:
                with anyio.fail_after(AGENT_TIMEOUT):
                    results[name] = await agent.run()
                print(f"  ✅ {agent.description} 에이전트 완료")
            except TimeoutError:
                print(f"  ⏰ {agent.description} 에이전트 타임아웃 ({AGENT_TIMEOUT}초 초과)")
                results[name] = {
                    "agent": name,
                    "error": f"timeout ({AGENT_TIMEOUT}s)",
                    "summary": f"에이전트 실행 타임아웃: {AGENT_TIMEOUT}초 초과",
                }
            except Exception as e:
                print(f"  ❌ {agent.description} 에이전트 실패: {e}")
                results[name] = {
                    "agent": name,
                    "error": str(e),
                    "summary": f"에이전트 실행 실패: {e}",
                }
            # 마지막 에이전트가 아니면 대기
            if i < len(phase1_agents) - 1:
                print(f"  ⏳ rate limit 방지 {RATE_LIMIT_SLEEP}초 대기...")
                await anyio.sleep(RATE_LIMIT_SLEEP)

        # Phase 2: 콘텐츠 전략 에이전트 (다른 에이전트 결과 참조)
        print(f"\n⏳ rate limit 방지 {RATE_LIMIT_SLEEP}초 대기...")
        await anyio.sleep(RATE_LIMIT_SLEEP)
        print("📡 Phase 2: 콘텐츠 전략 에이전트 실행 중...")
        context = {
            k: v.get("summary", "") for k, v in results.items() if "summary" in v
        }
        try:
            with anyio.fail_after(AGENT_TIMEOUT):
                results["content_strategy"] = await self.agents["content_strategy"].run(
                    context=context
                )
            print("  ✅ 콘텐츠 전략 에이전트 완료")
        except TimeoutError:
            print(f"  ⏰ 콘텐츠 전략 에이전트 타임아웃 ({AGENT_TIMEOUT}초 초과)")
            results["content_strategy"] = {
                "agent": "content_strategy",
                "error": f"timeout ({AGENT_TIMEOUT}s)",
                "summary": f"에이전트 실행 타임아웃: {AGENT_TIMEOUT}초 초과",
            }
        except Exception as e:
            print(f"  ❌ 콘텐츠 전략 에이전트 실패: {e}")
            results["content_strategy"] = {
                "agent": "content_strategy",
                "error": str(e),
                "summary": f"에이전트 실행 실패: {e}",
            }

        # Phase 3: 결과 종합 → 브리핑 생성
        print(f"\n⏳ rate limit 방지 {RATE_LIMIT_SLEEP}초 대기...")
        await anyio.sleep(RATE_LIMIT_SLEEP)
        print("📊 Phase 3: 결과 종합 브리핑 생성 중...")
        briefing = await self._generate_briefing(results)

        # 결과 저장
        self._save_results(results, briefing)

        return briefing

    async def _generate_briefing(self, results: dict) -> str:
        """에이전트 결과를 종합하여 브리핑 생성."""
        # 결과를 임시 파일로 저장하여 프롬프트 크기 절감
        OUTPUT_DIR.mkdir(exist_ok=True)
        temp_path = OUTPUT_DIR / "temp_agent_results.json"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        temp_path_str = str(temp_path).replace("\\", "/")

        today = date.today()
        weekdays = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
        weekday = weekdays[today.weekday()]
        prompt = (
            f"오늘은 {today.isoformat()} {weekday}입니다. "
            f"Read로 에이전트 분석 결과를 읽으세요: {temp_path_str} . "
            "결과를 종합하여 수익 중심 일일 전략 브리핑을 작성하세요. "
            "반드시 다음 5단 구조로 작성: "
            "(1) 오늘의 수익 대시보드: 에이전트별 파이프라인 매출/원가/수익/마진율 합산 테이블, "
            "(2) GO 리스트: GO/YES/TODAY/PROPOSE-TODAY/PUBLISH-TODAY 항목을 수익 크기 내림차순 정렬. "
            "각 항목에 [입찰/시세/소장/픽스맨/콘텐츠] 태그와 추천 액션 포함, "
            "(3) 객단가 상승 기회: 번들/크로스셀/업셀 통합. 기본주문 대비 추가매출 비율 표시, "
            "(4) 리스크 경고: 마진<15% 항목, 재고부족, 연락공백>=14일 고객, "
            "(5) 에이전트별 상세: 각 에이전트 결과 요약 + 수익정보. "
            "사람이 읽기 좋은 텍스트 브리핑으로 작성하세요 (JSON 아님). "
            "금액은 만원 단위로 표시하세요."
        )

        briefing_text = ""
        async for message in query(
            prompt=prompt,
            options=ClaudeCodeOptions(
                system_prompt=ORCHESTRATOR_PROMPT,
                model=MODEL,
                max_turns=5,
                allowed_tools=["Read"],
            ),
        ):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        briefing_text += block.text

        return briefing_text

    def _save_results(self, results: dict, briefing: str):
        """결과를 파일로 저장."""
        OUTPUT_DIR.mkdir(exist_ok=True)
        today = date.today().isoformat()

        # JSON 원본 저장
        raw_path = OUTPUT_DIR / f"raw_results_{today}.json"
        with open(raw_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n💾 원본 데이터 저장: {raw_path}")

        # 브리핑 텍스트 저장
        briefing_path = OUTPUT_DIR / f"briefing_{today}.txt"
        with open(briefing_path, "w", encoding="utf-8") as f:
            f.write(briefing)
        print(f"💾 브리핑 저장: {briefing_path}")


async def run_single_agent(agent_name: str) -> dict:
    """개별 에이전트 단독 실행."""
    orchestrator = DailyStrategyOrchestrator()
    if agent_name not in orchestrator.agents:
        available = ", ".join(orchestrator.agents.keys())
        raise ValueError(f"알 수 없는 에이전트: {agent_name}. 사용 가능: {available}")

    agent = orchestrator.agents[agent_name]
    print(f"▶ {agent.description} 에이전트 단독 실행 중...")
    result = await agent.run()
    print(f"✅ {agent.description} 에이전트 완료\n")
    return result
