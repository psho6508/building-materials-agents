"""Agent 3: 소장 CRM 에이전트.

현장소장 네트워크를 데이터화하고, 공정별 선제적 자재 제안을 수행한다.
"""

import json
import sys
from datetime import date
from pathlib import Path

import anyio
from claude_code_sdk import query, ClaudeCodeOptions, AssistantMessage, TextBlock

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DATA_DIR, MAX_TURNS, MODEL


# Windows에서 CLI 인자 줄바꿈 문제 방지: 한 줄로 작성
SYSTEM_PROMPT = (
    "당신은 건축자재 유통업체의 소장 관계관리(CRM) 전문가입니다. "
    "현장소장 데이터를 분석하여 선제적 자재 제안 타이밍을 포착합니다. "
    "공정별 필요자재: 기초공사-철근,시멘트,레미콘,거푸집 / 골조공사-철근,시멘트,레미콘,철골 / "
    "방수공사-방수시트,방수도료,실란트 / 배관공사-PVC파이프,동파이프,밸브류 / "
    "전기공사-전선,배선기구,조명기구,분전반 / 내장공사-석고보드,타일,도배지,바닥재 / "
    "외장공사-외장재,단열재,창호,유리 / 설비공사-보일러,에어컨배관,소방자재,위생도기 / "
    "마감공사-도료,실리콘,코킹재,하드웨어. "
    "긴급도 기준: 다음 공정 전환까지 2주 이내=긴급, 1개월 이내=중요, 그 외=참고."
)


class SiteManagerCRMAgent:
    """소장 CRM 에이전트."""

    def __init__(self):
        self.name = "site_manager_crm"
        self.description = "소장 CRM"

    async def run(self) -> dict:
        """에이전트 실행: 소장 데이터 분석 및 선제적 제안."""
        managers_path = str(DATA_DIR / "site_managers.json").replace("\\", "/")
        products_path = str(DATA_DIR / "products.json").replace("\\", "/")

        today = date.today().isoformat()
        prompt = (
            f"오늘은 {today}입니다. "
            f"Read 도구로 두 파일을 읽고 분석하세요. "
            f"소장 데이터: {managers_path} / "
            f"자재 카탈로그: {products_path} / "
            "각 소장별로 현재공정 진행률에서 다음 공정 전환 시점 예측, "
            "다음 공정 필요 자재를 카탈로그에서 매칭, "
            "선호 브랜드와 발주이력 반영 맞춤 제안, "
            "마지막 연락일 기준 연락 필요성 판단을 하세요. "
            'JSON 형식으로 응답하세요: '
            f'{{"agent":"site_manager_crm","timestamp":"{today}",'
            '"manager_actions":[{"manager_name":"소장명","site":"현장",'
            '"current_phase":"현재공정","next_phase":"다음공정",'
            '"next_materials":["자재"],"recommended_contact_date":"날짜",'
            '"proposal_content":"제안","urgency":"긴급/중요/참고",'
            '"relationship_note":"관계 포인트"}],"summary":"요약"}'
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
        """에이전트 출력에서 JSON 추출."""
        try:
            if "```json" in text:
                json_str = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                json_str = text.split("```")[1].split("```")[0].strip()
            else:
                json_str = text.strip()
            return json.loads(json_str)
        except (json.JSONDecodeError, IndexError):
            return {
                "agent": "site_manager_crm",
                "manager_actions": [],
                "summary": f"파싱 실패. 원본 응답: {text[:500]}",
                "raw_response": text,
            }


async def main():
    """단독 실행용."""
    agent = SiteManagerCRMAgent()
    result = await agent.run()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    anyio.run(main)
