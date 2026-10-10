"""승인된 후보에 대해 블로그 초안 / 영상 대본 초안을 생성한다.

네이버에는 공식 글쓰기 API가 없고, 유튜브 업로드는 OAuth 설정이 필요하므로
이 모듈은 '발행 가능한 완성 초안'까지만 만든다. 실제 발행/업로드는 사람이 한다.
"""

from anthropic import Anthropic

from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL, BRAND_CONTEXT, BRAND_NAME

BLOG_SYSTEM_PROMPT = (
    "당신은 철물/건축자재 유통업체의 네이버 블로그 전문 작가입니다. "
    f"{BRAND_CONTEXT} "
    "네이버 SEO(C-Rank/D.I.A.) 원칙을 지켜 2000~3000자 분량의 블로그 글을 작성하세요. "
    "제목에 핵심 키워드를 포함하고, 도입부-소제목 3~4개-결론-CTA 구조를 따르세요. "
    f"글 말미에 {BRAND_NAME} 자연스러운 언급과 방문/상담 유도 문구(CTA)를 포함하세요. "
    "과장 광고성 표현(최고, 1등, 완벽 등 단정적 표현)은 피하고 실용적이고 신뢰감 있는 톤을 유지하세요. "
    "이미지가 필요한 자리는 [이미지: 설명] 형식으로 표시하세요."
)

VIDEO_SYSTEM_PROMPT = (
    "당신은 철물/건축자재 유통업체의 숏폼(쇼츠) 영상 작가입니다. "
    f"{BRAND_CONTEXT} "
    "30~60초 분량의 숏폼 대본을 작성하세요. 구조: 후킹(3초 내 시선을 끄는 질문/상황)-"
    "문제 공감-해결/정보 제공(자재·제품·팁)-CTA. "
    "각 장면을 [장면 N | 자막 | 내레이션] 형식으로 구분하고, 과장 없이 실용적인 톤을 유지하세요."
)


def _call_claude(system_prompt: str, user_prompt: str) -> str:
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=4000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return "".join(block.text for block in message.content if hasattr(block, "text"))


def generate_blog_draft(candidate: dict) -> str:
    prompt = (
        f"주제 키워드: {candidate['topic']}\n"
        f"연결 이유: {candidate.get('reason', '')}\n"
        f"콘텐츠 각도: {candidate.get('angle', '')}\n\n"
        "위 내용을 바탕으로 블로그 글 전체를 작성하세요. 제목은 별도 줄에 '# '으로 시작하세요."
    )
    return _call_claude(BLOG_SYSTEM_PROMPT, prompt)


def generate_video_script(candidate: dict) -> str:
    prompt = (
        f"주제 키워드: {candidate['topic']}\n"
        f"연결 이유: {candidate.get('reason', '')}\n"
        f"콘텐츠 각도: {candidate.get('angle', '')}\n\n"
        "위 내용을 바탕으로 숏폼 대본 전체를 작성하세요. 제목(영상 제목 후보)은 별도 줄에 '# '으로 시작하세요."
    )
    return _call_claude(VIDEO_SYSTEM_PROMPT, prompt)
