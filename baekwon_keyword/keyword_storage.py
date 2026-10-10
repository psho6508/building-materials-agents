"""관련성 필터를 통과한 키워드를 일별 파일로 누적 저장한다.

승인/발송 여부와 무관하게, '백원철물건재와 연결된다'고 판단된 키워드는
모두 keyword_storage/{YYYY-MM-DD}.json 에 기록해 이력을 남긴다.
하루 4회 수집이 모두 같은 날짜 파일에 누적된다.
"""

import json

from config import KEYWORD_STORAGE_DIR


def _path_for(date_str: str):
    return KEYWORD_STORAGE_DIR / f"{date_str}.json"


def append_candidates(date_str: str, collected_at_iso: str, candidates: list[dict]):
    if not candidates:
        return

    KEYWORD_STORAGE_DIR.mkdir(exist_ok=True)
    path = _path_for(date_str)

    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"date": date_str, "entries": []}

    for c in candidates:
        data["entries"].append(
            {
                "collected_at": collected_at_iso,
                "id": c.get("id", ""),
                "topic": c["topic"],
                "source": c["source"],
                "rank": c.get("rank"),
                "reason": c.get("reason", ""),
                "angle": c.get("angle", ""),
                "suggested_action": c.get("suggested_action", ""),
            }
        )

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
