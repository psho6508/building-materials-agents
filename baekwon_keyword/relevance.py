"""수집된 원시 키워드 중 백원철물건재와 연결되는 주제를 Claude로 선별한다."""

import hashlib
import json

from anthropic import Anthropic

from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL, BRAND_CONTEXT, MAX_CANDIDATES_PER_RUN

SYSTEM_PROMPT = (
    "당신은 철물/건축자재 유통업체의 콘텐츠 기획자입니다. "
    f"{BRAND_CONTEXT} "
    "오늘의 실시간 트렌드 키워드 목록에서, 백원철물건재 고객이 실제로 겪는 생활 속 상황과 "
    "자연스럽게 연결되는 주제만 엄격하게 선별합니다. 좋은 예: 수전 고장, 전등 깜박임, 누수, "
    "동파, 정전, 곰팡이, 장마/한파로 인한 집수리 수요, 공구·자재 구매 고민, 동네 철물점 이용 등 "
    "구체적인 생활 수리/자재 상황. "
    "다음 유형은 억지로 연결고리를 만들지 말고 반드시 제외하세요: "
    "(1) 사고·재해·재난 뉴스(화재, 사망, 부상, 참사 등), "
    "(2) 정치 관련 키워드(정치인, 정당, 정책 이슈), "
    "(3) 연예인·유명인 이름이 포함된 키워드(가십, 스캔들, 근황 등). "
    "스포츠 결과, 단순 가십 등 생활 수리/자재와 무관한 항목도 제외하세요. "
    "확신이 없으면 포함시키지 말고, 적합한 주제가 없으면 빈 배열을 반환하세요."
)


def _candidate_id(source: str, keyword: str) -> str:
    return hashlib.md5(f"{source}:{keyword}".encode("utf-8")).hexdigest()[:10]


def _extract_json(text: str):
    try:
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        return json.loads(text.strip())
    except (json.JSONDecodeError, IndexError):
        pass
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass
    return []


def filter_candidates(raw_items: list[dict]) -> list[dict]:
    """raw_items: [{"keyword","rank","source"}, ...] → 선별된 후보 카드 리스트."""
    if not raw_items:
        return []
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY 가 설정되지 않았습니다.")

    numbered = "\n".join(
        f"{i+1}. [{item['source']}] {item['keyword']}" for i, item in enumerate(raw_items)
    )
    prompt = (
        f"아래는 오늘 수집된 실시간 트렌드 키워드 {len(raw_items)}개입니다:\n{numbered}\n\n"
        f"이 중 백원철물건재 콘텐츠 주제로 쓸 수 있는 것을 최대 {MAX_CANDIDATES_PER_RUN}개 골라 "
        "아래 JSON 배열 형식으로만 응답하세요 (설명 문장 없이 JSON만):\n"
        '[{"keyword":"원본 키워드","reason":"왜 연결되는지 1문장","angle":"콘텐츠 각도 1문장",'
        '"suggested_action":"blog 또는 video 또는 both"}]\n'
        "연결될 게 없으면 빈 배열 []을 반환하세요."
    )

    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(block.text for block in message.content if hasattr(block, "text"))
    picked = _extract_json(text)

    by_keyword = {item["keyword"]: item for item in raw_items}
    candidates = []
    for p in picked:
        kw = p.get("keyword", "")
        src_item = by_keyword.get(kw)
        if not src_item:
            # 모델이 키워드를 살짝 바꿔 반환한 경우를 대비한 느슨한 매칭
            src_item = next((it for it in raw_items if it["keyword"] in kw or kw in it["keyword"]), None)
        if not src_item:
            continue
        cid = _candidate_id(src_item["source"], src_item["keyword"])
        candidates.append(
            {
                "id": cid,
                "topic": src_item["keyword"],
                "source": src_item["source"],
                "rank": src_item["rank"],
                "reason": p.get("reason", ""),
                "angle": p.get("angle", ""),
                "suggested_action": p.get("suggested_action", "blog"),
            }
        )
    return candidates
