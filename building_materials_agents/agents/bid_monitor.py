"""Agent 1: 입찰/착공 감시 에이전트."""

import json
import sys
from datetime import date
from pathlib import Path

import anyio
from claude_code_sdk import query, ClaudeCodeOptions, AssistantMessage, TextBlock

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import MAX_TURNS, MODEL

SYSTEM_PROMPT = (
    "당신은 건축자재 유통업체의 입찰/착공 감시 전문가입니다. "
    "나라장터 입찰공고와 세움터 착공신고 정보를 검색하여 건축자재 영업 기회를 찾습니다. "
    "각 기회의 긴급도(긴급/중요/참고)와 추천 영업 액션을 판단합니다."
)


class BidMonitorAgent:
    def __init__(self):
        self.name = "bid_monitor"
        self.description = "입찰/착공 감시"

    async def run(self) -> dict:
        today = date.today().isoformat()
        prompt = (
            f"오늘은 {today}입니다. "
            'WebSearch로 "나라장터 입찰공고 건축자재 서울 2026" 검색하고, '
            '"세움터 착공신고 서울 2026" 도 검색하세요. '
            "결과에서 건축자재 영업 기회 3~5건 도출하세요. "
            f'JSON으로 응답: {{"agent":"bid_monitor","timestamp":"{today}",'
            '"opportunities":[{"title":"공고명","region":"지역","scale":"규모",'
            '"material_types":["자재"],"urgency":"긴급/중요/참고",'
            '"deadline":"마감일","recommended_action":"액션",'
            '"estimated_value":"예상규모"}],"summary":"요약"}'
        )

        result_text = ""
        async for message in query(
            prompt=prompt,
            options=ClaudeCodeOptions(
                system_prompt=SYSTEM_PROMPT,
                model=MODEL,
                max_turns=MAX_TURNS,
                allowed_tools=["WebSearch", "WebFetch"],
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
            return {"agent": "bid_monitor", "opportunities": [],
                    "summary": f"파싱 실패: {text[:500]}", "raw_response": text}

async def main():
    agent = BidMonitorAgent()
    result = await agent.run()
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    anyio.run(main)
