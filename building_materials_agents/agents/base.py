"""BaseAgent 추상 베이스 클래스.

모든 에이전트가 공유하는 SDK 호출 루프, JSON 파서, 유틸리티를 제공한다.
서브클래스는 클래스 속성과 build_prompt() 메서드만 구현하면 된다.
"""

import json
from abc import ABC, abstractmethod
from datetime import date

from claude_code_sdk import query, ClaudeCodeOptions, AssistantMessage, TextBlock

from config import DATA_DIR, MAX_TURNS, MODEL


class BaseAgent(ABC):
    """에이전트 추상 베이스 클래스.

    서브클래스 필수 구현:
        name (str): 에이전트 식별자 (예: "bid_monitor")
        description (str): 에이전트 설명 (예: "입찰/착공 감시")
        SYSTEM_PROMPT (str): 시스템 프롬프트 (개행 없는 단일 문자열)
        allowed_tools (list[str]): 허용 도구 목록
        fallback_result (dict): 파싱 실패 시 반환할 기본 dict
        build_prompt(**kwargs) -> str: 프롬프트 생성 메서드
    """

    name: str
    description: str
    SYSTEM_PROMPT: str
    allowed_tools: list[str]
    fallback_result: dict

    async def run(self, **kwargs) -> dict:
        """템플릿 메서드: build_prompt → _query_claude → _parse_result."""
        prompt = self.build_prompt(**kwargs)
        text = await self._query_claude(prompt)
        return self._parse_result(text)

    @abstractmethod
    def build_prompt(self, **kwargs) -> str:
        """SDK에 전달할 프롬프트를 생성한다.

        Windows 제약: 반환 문자열에 개행(\\n)을 포함하지 마세요.
        문자열 연결 ()을 사용하여 단일 줄로 작성합니다.
        """

    async def _query_claude(self, prompt: str) -> str:
        """SDK를 호출하고 텍스트 응답을 수집한다."""
        result_text = ""
        async for message in query(
            prompt=prompt,
            options=ClaudeCodeOptions(
                system_prompt=self.SYSTEM_PROMPT,
                model=MODEL,
                max_turns=MAX_TURNS,
                allowed_tools=self.allowed_tools,
            ),
        ):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        result_text += block.text
        return result_text

    def _parse_result(self, text: str) -> dict:
        """3단계 JSON 파서: 코드블록 → 전체 JSON → 중괄호 깊이추적."""
        # 1단계: 코드블록 추출
        try:
            if "```json" in text:
                json_str = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                json_str = text.split("```")[1].split("```")[0].strip()
            else:
                json_str = text.strip()
            return json.loads(json_str)
        except (json.JSONDecodeError, IndexError):
            pass

        # 2단계: 중괄호 깊이추적 — 텍스트 중간에 JSON이 있을 때
        try:
            start = text.index("{")
            depth, end = 0, start
            for i in range(start, len(text)):
                if text[i] == "{":
                    depth += 1
                elif text[i] == "}":
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break
            return json.loads(text[start:end])
        except (ValueError, json.JSONDecodeError):
            pass

        # 3단계: 폴백 — 기본 dict 반환
        fallback = dict(self.fallback_result)
        fallback["summary"] = f"파싱 실패: {text[:500]}"
        fallback["raw_response"] = text
        return fallback

    @staticmethod
    def _data_path(filename: str) -> str:
        """data 디렉토리 내 파일의 Windows-safe 경로를 반환한다."""
        return str(DATA_DIR / filename).replace("\\", "/")

    @staticmethod
    def today() -> str:
        """오늘 날짜를 ISO 형식으로 반환한다."""
        return date.today().isoformat()
