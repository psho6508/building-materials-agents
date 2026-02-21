"""Agent 5: 콘텐츠 전략 에이전트."""

import json
import sys
from datetime import date
from pathlib import Path

import anyio
from claude_code_sdk import query, ClaudeCodeOptions, AssistantMessage, TextBlock

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DATA_DIR, MAX_TURNS, MODEL

SYSTEM_PROMPT = (
    "당신은 건축자재 유통업체의 콘텐츠 전략 전문가입니다. "
    "건자재TV YouTube 채널의 콘텐츠를 매출로 연결하는 전략을 수립합니다. "
    "콘텐츠 유형: 자재 비교 리뷰, 시공 노하우, 시세 브리핑, 현장 사례."
)


class ContentStrategyAgent:
    def __init__(self):
        self.name = "content_strategy"
        self.description = "콘텐츠 전략"

    async def run(self, context: dict | None = None) -> dict:
        managers_path = str(DATA_DIR / "site_managers.json").replace("\\", "/")
        products_path = str(DATA_DIR / "products.json").replace("\\", "/")

        context_text = ""
        if context:
            context_text = f" 다른 에이전트 분석 요약: {json.dumps(context, ensure_ascii=False)} ."

        today = date.today().isoformat()
        prompt = (
            f"오늘은 {today}, 겨울~초봄입니다. "
            f"Read로 소장 데이터({managers_path})와 자재 데이터({products_path})를 읽으세요. "
            'WebSearch로 "건축자재 트렌드 2026" 검색하세요. '
            f"{context_text}"
            "매출 연결 가능한 콘텐츠 3~4개를 기획하세요. "
            f'JSON으로 응답: {{"agent":"content_strategy","timestamp":"{today}",'
            '"content_plans":[{"title":"제목","type":"비교리뷰/시공노하우/시세브리핑/현장사례",'
            '"target_managers":["소장명"],"channel":"YouTube/카카오톡/문자",'
            '"key_message":"핵심메시지","cta":"구매유도",'
            '"timing":"발행시기","urgency":"긴급/중요/참고"}],'
            '"weekly_calendar":"이번 주 일정","summary":"요약"}'
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
            return {"agent": "content_strategy", "content_plans": [],
                    "summary": f"파싱 실패: {text[:500]}", "raw_response": text}

async def main():
    agent = ContentStrategyAgent()
    result = await agent.run()
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    anyio.run(main)
