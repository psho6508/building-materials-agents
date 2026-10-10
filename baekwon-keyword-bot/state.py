"""상태 파일(JSON) 로드/저장.

GitHub Actions 러너는 실행마다 초기화되므로, pending_candidates.json과
telegram_offset.json을 저장소에 커밋해두고 다음 실행에서 다시 읽어온다.
"""

import json

from config import OFFSET_PATH, PENDING_PATH, SEEN_PATH, STATE_DIR


def load_pending() -> dict:
    STATE_DIR.mkdir(exist_ok=True)
    if not PENDING_PATH.exists():
        return {"candidates": {}}
    with open(PENDING_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_pending(data: dict):
    STATE_DIR.mkdir(exist_ok=True)
    with open(PENDING_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_offset() -> int:
    if not OFFSET_PATH.exists():
        return 0
    with open(OFFSET_PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("offset", 0)


def save_offset(offset: int):
    STATE_DIR.mkdir(exist_ok=True)
    with open(OFFSET_PATH, "w", encoding="utf-8") as f:
        json.dump({"offset": offset}, f, ensure_ascii=False, indent=2)


def load_seen_keywords() -> set[str]:
    """직전 수집 회차에서 본 '소스:키워드' 집합 — '새로 진입' 판정에 사용."""
    if not SEEN_PATH.exists():
        return set()
    with open(SEEN_PATH, "r", encoding="utf-8") as f:
        return set(json.load(f).get("keys", []))


def save_seen_keywords(keys: set[str]):
    STATE_DIR.mkdir(exist_ok=True)
    with open(SEEN_PATH, "w", encoding="utf-8") as f:
        json.dump({"keys": sorted(keys)}, f, ensure_ascii=False, indent=2)
