"""Agent 2: 시세 추적 에이전트."""

import json
import sys
from datetime import date
from pathlib import Path

import anyio
from claude_code_sdk import query, ClaudeCodeOptions, AssistantMessage, TextBlock

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DATA_DIR, MAX_TURNS, MODEL

SYSTEM_PROMPT = (
    "당신은 건축자재 유통업체의 시세 분석 전문가입니다. "
    "핵심 원자재의 시세 변동을 분석하고 매입/판매 전략을 제안합니다. "
    "판단기준: 5%이상 상승=매입확대(긴급), 2~5% 상승=단가인상검토(중요), "
    "+-2% 이내=현행유지(참고), 2~5% 하락=매입관망(참고), 5%이상 하락=할인판매(중요)."
)


class PriceTrackerAgent:
    def __init__(self):
        self.name = "price_tracker"
        self.description = "시세 추적"

    async def run(self) -> dict:
        products_path = str(DATA_DIR / "products.json").replace("\\", "/")
        today = date.today().isoformat()
        prompt = (
            f"오늘은 {today}입니다. "
            f"Read로 자재 카탈로그를 읽으세요: {products_path} . "
            'WebSearch로 "철근 시세 가격 2026년 2월" 검색하고, '
            '"구리 국제가격 동향 2026" 도 검색하세요. '
            "카탈로그 데이터와 검색 결과를 종합 분석하세요. "
            f'JSON으로 응답: {{"agent":"price_tracker","timestamp":"{today}",'
            '"price_analysis":[{"material":"자재명","current_price":"현재가",'
            '"change_pct":0.0,"trend":"상승/안정/하락",'
            '"recommendation":"매입확대/단가인상/현행유지/매입관망/할인판매",'
            '"action_detail":"구체적방안","urgency":"긴급/중요/참고"}],'
            '"market_outlook":"시장전망","summary":"요약"}'
        )

        result_text = ""
        async for message in query(
            prompt=prompt,
            options=ClaudeCodeOptions(
                system_prompt=SYSTEM_PROMPT,
                model=MODEL,
                max_turns=MAX_TURNS,
                allowed_tools=["WebSearch", "WebFetch", "Read"],
            ),
        ):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        result_text += block.text
        return self._parse_result(result_text)

    def _parse_result(self, text: str) -> dict:
        try:
            if "```json" in text:
                json_str = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                json_str = text.split("```")[1].split("```")[0].strip()
            else:
                json_str = text.strip()
            return json.loads(json_str)
        except (json.JSONDecodeError, IndexError):
            return {"agent": "price_tracker", "price_analysis": [],
                    "summary": f"파싱 실패: {text[:500]}", "raw_response": text}

async def main():
    agent = PriceTrackerAgent()
    result = await agent.run()
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    anyio.run(main)
