"""Agent 1: 입찰/착공 감시 에이전트 — 수익 중심."""

import json

import anyio

from .base import BaseAgent

SYSTEM_PROMPT = (
    "당신은 건축자재 유통업체의 입찰/착공 감시 전문가입니다. "
    "나라장터 입찰공고와 세움터 착공신고 정보를 검색하여 건축자재 영업 기회를 찾습니다. "
    "수익성 판단 기준: 마진율 20%이상=우선추진, 15~20%=조건부추진, 15%미만=재검토. "
    "GO/NO-GO 판단: 마진율>=15% AND 자사재고 납품가능 AND 마감 D-7 이내 → GO. "
    "자재 카탈로그의 cost_price, selling_price, margin_pct를 기반으로 "
    "각 기회의 예상 매출(estimated_revenue), 예상 원가(estimated_cost), "
    "예상 수익(estimated_profit), 마진율(margin_pct)을 계산하세요. "
    "번들 판매 가능한 교차판매 자재(cross_sell_items)와 추가 매출도 제시하세요."
)


class BidMonitorAgent(BaseAgent):
    name = "bid_monitor"
    description = "입찰/착공 감시"
    SYSTEM_PROMPT = SYSTEM_PROMPT
    allowed_tools = ["WebSearch", "WebFetch", "Read"]
    fallback_result = {"agent": "bid_monitor", "opportunities": []}

    def build_prompt(self, **kwargs) -> str:
        products_path = self._data_path("products.json")
        today = self.today()
        return (
            f"오늘은 {today}입니다. "
            f"Read로 자재 카탈로그를 읽으세요: {products_path} . "
            'WebSearch로 "나라장터 입찰공고 건축자재 서울 2026" 검색하고, '
            '"세움터 착공신고 서울 2026" 도 검색하세요. '
            "결과에서 건축자재 영업 기회 3~5건 도출하세요. "
            "각 기회에 대해 자재 카탈로그의 cost_price와 selling_price를 참조하여 "
            "예상 매출/원가/수익/마진율을 계산하고, GO/NO-GO를 판단하세요. "
            "교차판매 자재(bundle_candidates)를 활용한 추가 매출도 제시하세요. "
            f'JSON으로 응답: {{"agent":"bid_monitor","timestamp":"{today}",'
            '"opportunities":[{"title":"공고명","region":"지역","scale":"규모",'
            '"material_types":["자재"],"urgency":"긴급/중요/참고",'
            '"deadline":"마감일","recommended_action":"액션",'
            '"estimated_revenue":0,"estimated_cost":0,"estimated_profit":0,'
            '"margin_pct":0.0,"go_no_go":"GO/NO-GO/재검토",'
            '"cross_sell_items":["교차판매자재"],"cross_sell_revenue":0}],'
            '"summary":"요약"}'
        )


async def main():
    agent = BidMonitorAgent()
    result = await agent.run()
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    anyio.run(main)
