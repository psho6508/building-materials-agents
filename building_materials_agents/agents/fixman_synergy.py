"""Agent 4: 픽스맨 연동 에이전트."""

import json
import sys
from datetime import date
from pathlib import Path

import anyio
from claude_code_sdk import query, ClaudeCodeOptions, AssistantMessage, TextBlock

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DATA_DIR, MAX_TURNS, MODEL

SYSTEM_PROMPT = (
    "당신은 건축자재 유통업체의 픽스맨 연동 전문가입니다. "
    "점검 리포트를 분석하여 자재 수요를 감지하고 번들 패키지를 구성합니다. "
    "패키지 할인: 2개 카테고리 이상 동시발주 5%할인, 3개 이상 8%할인, "
    "긴급+예방 교체 동시 3% 추가할인."
)


class FixmanSynergyAgent:
    def __init__(self):
        self.name = "fixman_synergy"
        self.description = "픽스맨 연동"

    async def run(self) -> dict:
        reports_path = str(DATA_DIR / "fixman_reports.json").replace("\\", "/")
        products_path = str(DATA_DIR / "products.json").replace("\\", "/")
        today = date.today().isoformat()
        prompt = (
            f"오늘은 {today}입니다. "
            f"Read로 두 파일을 읽으세요. "
            f"픽스맨 점검 리포트: {reports_path} / "
            f"자재 카탈로그: {products_path} . "
            "각 현장별로 긴급/보통 교체 항목을 자재와 매칭하고, "
            "번들 패키지를 구성하여 할인율을 적용하세요. "
            f'JSON으로 응답: {{"agent":"fixman_synergy","timestamp":"{today}",'
            '"site_packages":[{"site_name":"현장명","contact":"담당자",'
            '"urgent_items":[{"item":"항목","materials":["자재"],'
            '"estimated_cost":0,"urgency":"긴급/보통"}],'
            '"package_proposal":{"package_name":"패키지명",'
            '"total_before_discount":0,"discount_rate":"할인율",'
            '"total_after_discount":0,"items_included":["항목"],'
            '"value_proposition":"어필포인트"},'
            '"recommended_action":"액션","urgency":"긴급/중요/참고"}],"summary":"요약"}'
        )

        result_text = ""
        async for message in query(
            prompt=prompt,
            options=ClaudeCodeOptions(
                system_prompt=SYSTEM_PROMPT,
                model=MODEL,
                max_turns=MAX_TURNS,
                allowed_tools=["Read"],
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
            return {"agent": "fixman_synergy", "site_packages": [],
                    "summary": f"파싱 실패: {text[:500]}", "raw_response": text}

async def main():
    agent = FixmanSynergyAgent()
    result = await agent.run()
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    anyio.run(main)
