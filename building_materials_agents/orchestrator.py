"""Daily Strategy Orchestrator.

5개 에이전트를 병렬 실행하고, 결과를 종합하여 일일 전략 브리핑을 생성한다.
"""

import json
import sys
from datetime import date
from pathlib import Path

import anyio
from claude_code_sdk import query, ClaudeCodeOptions, AssistantMessage, TextBlock

from config import MAX_TURNS, MODEL, OUTPUT_DIR
from agents import (
    BidMonitorAgent,
    ContentStrategyAgent,
    FixmanSynergyAgent,
    PriceTrackerAgent,
    SiteManagerCRMAgent,
)


ORCHESTRATOR_PROMPT = (
    "당신은 건축자재 유통업체의 일일 전략 총괄 디렉터입니다. "
    "5개 에이전트 결과를 종합하여 브리핑을 작성합니다. "
    "우선순위: 긴급(입찰마감 D-3, 가격 5%급변, 긴급점검, 공정전환 D-7) / "
    "중요(입찰마감 D-7, 가격 2~5%변동, 보통점검, 공정전환 D-14) / "
    "참고(장기모니터링, 콘텐츠발행, 관계관리). "
    "금액은 만원 단위로 표시하세요."
)


class DailyStrategyOrchestrator:
    """일일 전략 오케스트레이터."""

    def __init__(self):
        self.agents = {
            "bid_monitor": BidMonitorAgent(),
            "price_tracker": PriceTrackerAgent(),
            "site_manager_crm": SiteManagerCRMAgent(),
            "fixman_synergy": FixmanSynergyAgent(),
            "content_strategy": ContentStrategyAgent(),
        }

    async def run(self) -> str:
        """5개 에이전트를 병렬 실행 후 결과 종합."""
        print("=" * 50)
        print("🚀 일일 전략 브리핑 생성을 시작합니다...")
        print("=" * 50)

        # Phase 1: 4개 에이전트 병렬 실행 (콘텐츠 전략은 다른 결과를 참고)
        print("\n📡 Phase 1: 4개 에이전트 병렬 실행 중...")
        results = {}

        async with anyio.create_task_group() as tg:
            async def run_agent(name, agent, **kwargs):
                print(f"  ▶ {agent.description} 에이전트 시작...")
                try:
                    results[name] = await agent.run(**kwargs)
                    print(f"  ✅ {agent.description} 에이전트 완료")
                except Exception as e:
                    print(f"  ❌ {agent.description} 에이전트 실패: {e}")
                    results[name] = {
                        "agent": name,
                        "error": str(e),
                        "summary": f"에이전트 실행 실패: {e}",
                    }

            tg.start_soon(run_agent, "bid_monitor", self.agents["bid_monitor"])
            tg.start_soon(run_agent, "price_tracker", self.agents["price_tracker"])
            tg.start_soon(run_agent, "site_manager_crm", self.agents["site_manager_crm"])
            tg.start_soon(run_agent, "fixman_synergy", self.agents["fixman_synergy"])

        # Phase 2: 콘텐츠 전략 에이전트 (다른 에이전트 결과 참조)
        print("\n📡 Phase 2: 콘텐츠 전략 에이전트 실행 중...")
        context = {
            k: v.get("summary", "") for k, v in results.items() if "summary" in v
        }
        try:
            results["content_strategy"] = await self.agents["content_strategy"].run(
                context=context
            )
            print("  ✅ 콘텐츠 전략 에이전트 완료")
        except Exception as e:
            print(f"  ❌ 콘텐츠 전략 에이전트 실패: {e}")
            results["content_strategy"] = {
                "agent": "content_strategy",
                "error": str(e),
                "summary": f"에이전트 실행 실패: {e}",
            }

        # Phase 3: 결과 종합 → 브리핑 생성
        print("\n📊 Phase 3: 결과 종합 브리핑 생성 중...")
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
            "결과를 종합하여 일일 전략 브리핑을 작성하세요. "
            "긴급도별 분류, [입찰/시세/소장/픽스맨/콘텐츠] 태그, "
            "각 항목에 추천 액션, 예상 매출 기회 합산을 포함하세요. "
            "사람이 읽기 좋은 텍스트 브리핑으로 작성하세요 (JSON 아님)."
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
