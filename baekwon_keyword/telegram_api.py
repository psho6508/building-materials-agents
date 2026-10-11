"""텔레그램 봇 API 래퍼 — 후보 카드 발송 + 버튼 콜백 수신.

키워드/Claude 생성 텍스트에는 <, >, & 등이 섞일 수 있어 parse_mode를 쓰지 않고
항상 평문으로 보낸다 (HTML 파싱 오류로 발송이 실패하는 것을 방지).
"""

import requests

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

API_BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
TG_LIMIT = 3800  # 텔레그램 메시지 최대 4096자 → 여유 두고 분할


def _check_config():
    if not (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID):
        raise RuntimeError("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID 가 설정되지 않았습니다.")


def _raise_with_body(resp: requests.Response):
    """실패 응답의 본문(에러 사유)을 로그로 남긴 뒤 예외를 던진다."""
    if not resp.ok:
        print(f"[텔레그램 API 오류] {resp.status_code}: {resp.text[:500]}")
    resp.raise_for_status()


def _send_with_keyboard(text: str, keyboard: dict) -> int | None:
    _check_config()
    resp = requests.post(
        f"{API_BASE}/sendMessage",
        json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "reply_markup": keyboard},
        timeout=20,
    )
    _raise_with_body(resp)
    result = resp.json()
    if result.get("ok"):
        return result["result"]["message_id"]
    return None


def send_candidate_card(candidate_id: str, text: str) -> int | None:
    """후보 카드 1건을 인라인 버튼과 함께 발송하고 message_id를 반환한다."""
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "📝 글 발행", "callback_data": f"blog:{candidate_id}"},
                {"text": "🎬 숏폼 제작", "callback_data": f"video:{candidate_id}"},
            ],
            [
                {"text": "🔀 둘 다", "callback_data": f"both:{candidate_id}"},
                {"text": "❌ 넘김", "callback_data": f"reject:{candidate_id}"},
            ],
        ]
    }
    return _send_with_keyboard(text, keyboard)


def send_video_review_card(candidate_id: str, text: str) -> int | None:
    """영상 대본 승인 카드를 인라인 버튼과 함께 발송하고 message_id를 반환한다."""
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "🎬 영상 만들기", "callback_data": f"mkvid:{candidate_id}"},
                {"text": "❌ 취소", "callback_data": f"cancelvid:{candidate_id}"},
            ]
        ]
    }
    return _send_with_keyboard(text, keyboard)


def send_text(text: str, reply_to_message_id: int | None = None):
    _check_config()
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    if reply_to_message_id:
        payload["reply_to_message_id"] = reply_to_message_id
    resp = requests.post(f"{API_BASE}/sendMessage", json=payload, timeout=20)
    _raise_with_body(resp)


def send_long_text(text: str):
    """4096자 제한을 넘는 긴 텍스트를 줄 단위로 나눠 여러 메시지로 발송한다."""
    chunks, cur = [], ""
    for line in text.split("\n"):
        if len(cur) + len(line) + 1 > TG_LIMIT:
            chunks.append(cur)
            cur = ""
        cur += line + "\n"
    if cur.strip():
        chunks.append(cur)
    for c in chunks:
        send_text(c)


def edit_message(
    message_id: int, text: str, remove_keyboard: bool = True, keyboard: dict | None = None
):
    _check_config()
    payload = {"chat_id": TELEGRAM_CHAT_ID, "message_id": message_id, "text": text}
    if keyboard is not None:
        payload["reply_markup"] = keyboard
    elif remove_keyboard:
        payload["reply_markup"] = {"inline_keyboard": []}
    resp = requests.post(f"{API_BASE}/editMessageText", json=payload, timeout=20)
    if not resp.ok:
        print(f"[경고] 메시지 수정 실패: {resp.text[:300]}")


def answer_callback(callback_query_id: str, text: str = ""):
    _check_config()
    requests.post(
        f"{API_BASE}/answerCallbackQuery",
        json={"callback_query_id": callback_query_id, "text": text},
        timeout=20,
    )


def get_updates(offset: int) -> list[dict]:
    """offset 이후의 업데이트(버튼 콜백 포함)를 가져온다."""
    _check_config()
    resp = requests.get(
        f"{API_BASE}/getUpdates",
        params={"offset": offset, "timeout": 0},
        timeout=20,
    )
    _raise_with_body(resp)
    result = resp.json()
    if result.get("ok"):
        return result["result"]
    return []
