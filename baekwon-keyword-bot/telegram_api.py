"""텔레그램 봇 API 래퍼 — 후보 카드 발송 + 버튼 콜백 수신."""

import requests

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

API_BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def _check_config():
    if not (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID):
        raise RuntimeError("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID 가 설정되지 않았습니다.")


def send_candidate_card(candidate_id: str, text: str) -> int | None:
    """후보 카드 1건을 인라인 버튼과 함께 발송하고 message_id를 반환한다."""
    _check_config()
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "📝 블로그 발행", "callback_data": f"blog:{candidate_id}"},
                {"text": "🎬 영상 제작", "callback_data": f"video:{candidate_id}"},
                {"text": "❌ 거절", "callback_data": f"reject:{candidate_id}"},
            ]
        ]
    }
    resp = requests.post(
        f"{API_BASE}/sendMessage",
        json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "reply_markup": keyboard,
            "parse_mode": "HTML",
        },
        timeout=20,
    )
    resp.raise_for_status()
    result = resp.json()
    if result.get("ok"):
        return result["result"]["message_id"]
    return None


def send_text(text: str, reply_to_message_id: int | None = None):
    _check_config()
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
    if reply_to_message_id:
        payload["reply_to_message_id"] = reply_to_message_id
    resp = requests.post(f"{API_BASE}/sendMessage", json=payload, timeout=20)
    resp.raise_for_status()


def edit_message(message_id: int, text: str, remove_keyboard: bool = True):
    _check_config()
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML",
    }
    if remove_keyboard:
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
    resp.raise_for_status()
    result = resp.json()
    if result.get("ok"):
        return result["result"]
    return []
