"""Agent 2: 시세 전략 에이전트 — 4대 자재 카테고리 시세 분석 + 마진 잠식 판단."""

import json

import anyio

from .base import BaseAgent
from config import MATERIAL_CATEGORIES, MARGIN_EROSION_THRESHOLDS

SYSTEM_PROMPT = (
    "당신은 건축자재 유통업체(백원철물건재)의 4대 자재 카테고리 시세 분석 전문가입니다. "
    "4대 카테고리: 단열재, 철강재, 철물자재, 건축자재. "
    "카테고리별 시세 변동을 분석하고, 재고 가치 변동과 마진 잠식액을 계산합니다. "
    "DO/HOLD/SKIP 판단 기준: "
    "DO(단가인상)=마진 잠식 3%p 이상이면 거래처 단가 인상 필요, "
    "HOLD(관찰)=마진 잠식 1~3%p이면 추이 관찰, "
    "SKIP(조치불필요)=마진 잠식 1%p 미만. "
    "재고부족 경고: inventory_qty < reorder_point이면 stock_alert=true. "
    "반드시 JSON으로만 응답하세요. 코드블록(```)없이 순수 JSON만 출력하세요."
)


class PriceStrategyAgent(BaseAgent):
    name = "price_strategy"
    description = "시세 전략 (4대 카테고리)"
    SYSTEM_PROMPT = SYSTEM_PROMPT
    allowed_tools = ["WebSearch", "Read"]
    fallback_result = {"agent": "price_strategy", "category_analysis": []}

    def build_prompt(self, **kwargs) -> str:
        products_path = self._data_path("products.json")
        today = self.today()
        return (
            f"오늘은 {today}입니다. "
            f"Read로 자재 카탈로그를 읽으세요: {products_path} . "
            'WebSearch로 "건축자재 시세 철근 단열재 시멘트 가격 동향 2026"을 검색하세요. '
            "검색 결과와 자재 데이터를 기반으로 4대 카테고리별 시세 분석을 수행하세요. "
            "카테고리 매핑: "
            "단열재=P008(압출법 단열재), "
            "철강재=P001(철근 SD400 D10)+P002(철근 SD400 D16), "
            "철물자재=P003(시멘트)+P004(PVC파이프)+P005(동파이프), "
            "건축자재=P006(방수시트)+P007(석고보드)+P009(페인트)+P010(LED조명)+P011(양변기)+P012(시스템창호). "
            "각 품목의 시세 변동률(change_pct)을 기반으로 원가 변동을 추정하고, "
            "current_margin_pct = (selling_price - cost_price) / selling_price * 100, "
            "projected_margin_pct = (selling_price - cost_price * (1 + change_pct/100)) / selling_price * 100, "
            "마진 잠식 = current_margin_pct - projected_margin_pct 로 계산하세요. "
            "monthly_margin_erosion = 카테고리 내 품목별 (cost_price * change_pct/100 * inventory_qty) 합산. "
            "inventory_qty < reorder_point이면 stock_alert=true. "
            f"DO(단가인상): 마진 잠식 {MARGIN_EROSION_THRESHOLDS['DO']}%p 이상, "
            f"HOLD(관찰): 마진 잠식 {MARGIN_EROSION_THRESHOLDS['HOLD_MIN']}~{MARGIN_EROSION_THRESHOLDS['DO']}%p, "
            f"SKIP(조치불필요): 마진 잠식 {MARGIN_EROSION_THRESHOLDS['HOLD_MIN']}%p 미만. "
            "각 카테고리에 DO일 때 거래처에 보낼 단가 인상 안내 메시지를 action_message에 작성하세요. "
            "JSON 형식: "
            f'{{"agent":"price_strategy","timestamp":"{today}",'
            '"category_analysis":['
            '{"category":"카테고리명","representative_items":['
            '{"product_id":"P00X","name":"품명","current_price":0,"change_pct":0.0,"trend":"상승/안정/하락",'
            '"cost_price":0,"selling_price":0,"current_margin_pct":0.0,"projected_margin_pct":0.0,'
            '"inventory_qty":0,"reorder_point":0,"inventory_value_change":0,"stock_alert":false}],'
            '"monthly_margin_erosion":0,"decision":"DO/HOLD/SKIP","decision_reason":"판단 근거","action_message":"거래처 발송 메시지"}],'
            '"total_monthly_margin_erosion":0,"market_outlook":"시장 전망","summary":"요약"}'
        )


async def main():
    agent = PriceStrategyAgent()
    result = await agent.run()
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    anyio.run(main)
