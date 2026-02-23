"""Agent 5: 콘텐츠 전략 에이전트 — 수익 중심."""

import json

import anyio

from .base import BaseAgent

SYSTEM_PROMPT = (
    "당신은 건축자재 유통업체의 콘텐츠 전략 전문가입니다. "
    "건자재TV YouTube 채널의 콘텐츠를 매출/수익으로 연결하는 전략을 수립합니다. "
    "콘텐츠 ROI 계산: (타겟 매출 x 전환율 x 마진율) / 제작비(50만원). "
    "제품 티어: good(기본)/better(중급)/best(프리미엄) 3단계 추천으로 객단가 상승 유도. "
    "PUBLISH-TODAY 판단: 타겟 소장의 공정전환 D-14 이내 AND 관련 자재 가격변동>=3%. "
    "PUBLISH-WEEK: 공정전환 D-30 이내 OR 가격변동>=2%. "
    "BACKLOG: 그 외. "
    "콘텐츠 유형: 자재 비교 리뷰, 시공 노하우, 시세 브리핑, 현장 사례."
)


class ContentStrategyAgent(BaseAgent):
    name = "content_strategy"
    description = "콘텐츠 전략"
    SYSTEM_PROMPT = SYSTEM_PROMPT
    allowed_tools = ["WebSearch", "WebFetch", "Read"]
    fallback_result = {"agent": "content_strategy", "content_plans": []}

    def build_prompt(self, context: dict | None = None, **kwargs) -> str:
        managers_path = self._data_path("site_managers.json")
        products_path = self._data_path("products.json")
        today = self.today()

        context_text = ""
        if context:
            context_text = f" 다른 에이전트 분석 요약: {json.dumps(context, ensure_ascii=False)} ."

        return (
            f"오늘은 {today}, 겨울~초봄입니다. "
            f"Read로 소장 데이터({managers_path})와 자재 데이터({products_path})를 읽으세요. "
            'WebSearch로 "건축자재 트렌드 2026" 검색하세요. '
            f"{context_text}"
            "매출/수익 연결 가능한 콘텐츠 3~4개를 기획하세요. "
            "각 콘텐츠별로: (1) 타겟 소장과 공정전환 일정 확인, "
            "(2) 관련 자재의 selling_price, margin_pct로 target_revenue 계산, "
            "(3) 콘텐츠 ROI = (target_revenue x expected_conversion_rate x avg_margin_pct) / 500000, "
            "(4) good/better/best 3단계 제품 티어 구성, "
            "(5) 번들 CTA(bundle_cta) 포함, "
            "(6) PUBLISH-TODAY / PUBLISH-WEEK / BACKLOG 판단. "
            f'JSON으로 응답: {{"agent":"content_strategy","timestamp":"{today}",'
            '"content_plans":[{{"title":"제목","type":"비교리뷰/시공노하우/시세브리핑/현장사례",'
            '"target_managers":["소장명"],"channel":"YouTube/카카오톡/문자",'
            '"target_revenue":0,"expected_conversion_rate":0.0,'
            '"expected_profit":0,"content_roi":0.0,'
            '"product_tiers":{{"good":"기본","better":"중급","best":"프리미엄"}},'
            '"bundle_cta":"번들구매유도문구",'
            '"publish_decision":"PUBLISH-TODAY/PUBLISH-WEEK/BACKLOG",'
            '"key_message":"핵심메시지","timing":"발행시기"}}],'
            '"weekly_calendar":"이번 주 일정","summary":"요약"}'
        )


async def main():
    agent = ContentStrategyAgent()
    result = await agent.run()
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    anyio.run(main)
