"""Agent 2: 시세 추적 에이전트 — 수익 중심."""

import json

import anyio

from .base import BaseAgent

SYSTEM_PROMPT = (
    "당신은 건축자재 유통업체의 시세 분석 전문가입니다. "
    "자재 카탈로그에 cost_price(매입가), selling_price(판매가), margin_pct(마진율), "
    "inventory_qty(재고수량), reorder_point(재발주점), bundle_candidates(교차판매자재ID)가 있습니다. "
    "분석 기준: (1) 현재마진 = (selling_price - cost_price) / selling_price * 100, "
    "(2) 시세 변동 반영 예상마진(projected_margin_pct) 계산, "
    "(3) 재고수익기회 = inventory_qty * (selling_price - cost_price). "
    "YES/NO 매입판단: 마진율>=15% AND (가격상승추세 OR inventory_qty<=reorder_point) → YES. "
    "재고부족 경고: inventory_qty < reorder_point인 품목 강조. "
    "번들제안: bundle_candidates 활용 교차판매 추천."
)


class PriceTrackerAgent(BaseAgent):
    name = "price_tracker"
    description = "시세 추적"
    SYSTEM_PROMPT = SYSTEM_PROMPT
    allowed_tools = ["WebSearch", "WebFetch", "Read"]
    fallback_result = {"agent": "price_tracker", "price_analysis": []}

    def build_prompt(self, **kwargs) -> str:
        products_path = self._data_path("products.json")
        today = self.today()
        return (
            f"오늘은 {today}입니다. "
            f"Read로 자재 카탈로그를 읽으세요: {products_path} . "
            'WebSearch로 "철근 시세 가격 2026년 2월" 검색하고, '
            '"구리 국제가격 동향 2026" 도 검색하세요. '
            "카탈로그의 cost_price, selling_price, margin_pct, "
            "inventory_qty, reorder_point 데이터와 검색 결과를 종합 분석하세요. "
            "각 자재별 현재마진, 시세반영 예상마진, 재고수익기회를 계산하고, "
            "inventory_qty < reorder_point인 품목은 재고부족 경고하세요. "
            "bundle_candidates를 활용한 교차판매 번들도 제안하세요. "
            f'JSON으로 응답: {{"agent":"price_tracker","timestamp":"{today}",'
            '"price_analysis":[{"material":"자재명","product_id":"P00X",'
            '"current_price":"현재시세","change_pct":0.0,"trend":"상승/안정/하락",'
            '"cost_price":0,"selling_price":0,"current_margin_pct":0.0,'
            '"projected_margin_pct":0.0,"inventory_qty":0,"reorder_point":0,'
            '"inventory_profit_opportunity":0,'
            '"buy_now":"YES/NO","buy_reason":"판단근거",'
            '"bundle_suggestion":["번들자재"],'
            '"urgency":"긴급/중요/참고"}],'
            '"market_outlook":"시장전망","summary":"요약"}'
        )


async def main():
    agent = PriceTrackerAgent()
    result = await agent.run()
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    anyio.run(main)
