"""Agent 4: 픽스맨 연동 에이전트 — 수익 중심."""

import json

import anyio

from .base import BaseAgent

SYSTEM_PROMPT = (
    "당신은 건축자재 유통업체의 픽스맨 연동 전문가입니다. "
    "점검 리포트에 conversion_probability(수주전환율), decision_maker_authority(의사결정권한), "
    "follow_up_deadline(후속연락기한)이 있습니다. "
    "각 항목에 material_quantities(제품ID,수량,단가), total_material_cost, total_selling_price, "
    "profit_opportunity, margin_pct가 있습니다. "
    "패키지 할인: 2개 카테고리 이상 동시발주 5%, 3개 이상 8%, 긴급+예방 동시 3% 추가. "
    "마진 검증 게이트: 할인 적용 후에도 마진율 15% 이상이면 PASS, 미만이면 FAIL. "
    "PROPOSE-TODAY 판단: 긴급항목>=1 AND conversion>=0.7 AND 할인후마진>=15%. "
    "PROPOSE-WEEK: 긴급없고 conversion>=0.5 AND 할인후마진>=15%. "
    "HOLD: 그 외. "
    "업셀(upsell_items): 예방교체/업그레이드 자재 추가 제안."
)


class FixmanSynergyAgent(BaseAgent):
    name = "fixman_synergy"
    description = "픽스맨 연동"
    SYSTEM_PROMPT = SYSTEM_PROMPT
    allowed_tools = ["Read"]
    fallback_result = {"agent": "fixman_synergy", "site_packages": []}

    def build_prompt(self, **kwargs) -> str:
        reports_path = self._data_path("fixman_reports.json")
        products_path = self._data_path("products.json")
        today = self.today()
        return (
            f"오늘은 {today}입니다. "
            f"Read로 두 파일을 읽으세요. "
            f"픽스맨 점검 리포트: {reports_path} / "
            f"자재 카탈로그: {products_path} . "
            "각 현장별로: (1) conversion_probability, decision_maker_authority 확인, "
            "(2) 각 항목의 material_quantities로 total_material_cost, total_selling_price, "
            "profit_opportunity, margin_pct 검증, "
            "(3) 번들 패키지 구성 후 할인율 적용, "
            "(4) 할인 후 최종 마진율(final_margin_pct) 계산 → PASS/FAIL 판정, "
            "(5) PROPOSE-TODAY / PROPOSE-WEEK / HOLD 판단, "
            "(6) 예방교체/업그레이드 업셀 자재(upsell_items) 추가 제안. "
            f'JSON으로 응답: {{"agent":"fixman_synergy","timestamp":"{today}",'
            '"site_packages":[{{"site_name":"현장명","contact":"담당자",'
            '"conversion_probability":0.0,"decision_maker":"결재권한",'
            '"follow_up_deadline":"기한",'
            '"items":[{{"item":"항목","urgency":"긴급/보통",'
            '"material_cost":0,"selling_price":0,"profit":0,"margin_pct":0.0}}],'
            '"upsell_items":[{{"item":"업셀항목","type":"예방교체/업그레이드",'
            '"selling_price":0,"profit":0}}],'
            '"package_proposal":{{"package_name":"패키지명",'
            '"total_before_discount":0,"discount_rate":"할인율",'
            '"total_after_discount":0,"items_included":["항목"]}},'
            '"final_profit":0,"final_margin_pct":0.0,'
            '"margin_check":"PASS/FAIL",'
            '"propose_decision":"PROPOSE-TODAY/PROPOSE-WEEK/HOLD",'
            '"recommended_action":"액션"}}],"summary":"요약"}'
        )


async def main():
    agent = FixmanSynergyAgent()
    result = await agent.run()
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    anyio.run(main)
