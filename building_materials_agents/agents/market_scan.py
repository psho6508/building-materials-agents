"""Agent 1: 시장 스캔 에이전트 — 서울/경기 착공·입찰 감시."""

import json

import anyio

from .base import BaseAgent
from config import MARKET_SCAN_REGION, MATERIAL_CATEGORIES, DECISION_MARGIN_THRESHOLDS

SYSTEM_PROMPT = (
    "당신은 건축자재 유통업체(백원철물건재)의 서울/경기 착공·입찰 감시 전문가입니다. "
    "나라장터 입찰공고와 세움터 착공신고를 검색하여 건축자재 영업 기회를 찾습니다. "
    "4대 자재 카테고리(단열재, 철강재, 철물자재, 건축자재) 중심으로 자재 소요를 추정합니다. "
    "DO/HOLD/SKIP 판단: DO=마진200만원이상(무조건) 또는 마진100만원이상+서울경기+납기2주이상, HOLD=마진50~100만원, SKIP=마진50만원미만 또는 서울경기외. "
    "3단계 번들: basic=핵심자재만, recommended=핵심+보조, premium=전카테고리 풀패키지. "
    "반드시 JSON으로만 응답하세요. 코드블록(```)없이 순수 JSON만 출력하세요."
)


class MarketScanAgent(BaseAgent):
    name = "market_scan"
    description = "시장 스캔 (서울/경기)"
    SYSTEM_PROMPT = SYSTEM_PROMPT
    allowed_tools = ["WebSearch", "Read"]
    fallback_result = {"agent": "market_scan", "opportunities": []}

    def build_prompt(self, **kwargs) -> str:
        products_path = self._data_path("products.json")
        today = self.today()
        return (
            f"오늘은 {today}입니다. "
            f"Read로 자재 카탈로그를 읽으세요: {products_path} . "
            'WebSearch로 "나라장터 입찰공고 건축자재 서울 경기 2026"을 검색하세요. '
            "검색 결과에서 서울/경기 건축자재 영업 기회 3건을 도출하고, "
            "각 기회의 연면적 기반 4대 카테고리별 자재 소요량과 매출/원가/수익/마진율을 계산하고 DO/HOLD/SKIP 판단하세요. "
            "JSON 형식: "
            f'{{"agent":"market_scan","timestamp":"{today}","scan_region":"서울/경기",'
            '"opportunities":[{"title":"","source":"","region":"","building_type":"","scale":"",'
            '"construction_company":"","materials_by_category":{"단열재":{"items":[],"estimated_revenue":0},"철강재":{"items":[],"estimated_revenue":0},"철물자재":{"items":[],"estimated_revenue":0},"건축자재":{"items":[],"estimated_revenue":0}},'
            '"estimated_revenue":0,"estimated_cost":0,"estimated_profit":0,"margin_pct":0.0,'
            '"bundle_proposal":{"basic":{"items":[],"revenue":0},"recommended":{"items":[],"revenue":0},"premium":{"items":[],"revenue":0}},'
            '"decision":"","decision_reason":"","urgency":"","deadline":"","suggested_action":""}],"summary":""}'
        )


async def main():
    agent = MarketScanAgent()
    result = await agent.run()
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    anyio.run(main)
