"""하루 4회 실행: 4개 소스 수집 → 전체 목록 발송 → 관련성 필터링 → 후보 카드 발송.

GitHub Actions 워크플로우(baekwon-keyword-collect.yml)에서 호출된다.
"""

import hashlib
import os
from datetime import datetime, timezone, timedelta

import keyword_storage
import relevance
import sources
import state
import telegram_api
from config import MAX_CANDIDATES_PER_RUN

SOURCE_LABELS = {
    "nate_issue": "네이트 실시간 이슈",
    "zum_ai_trend": "줌 AI 이슈트렌드",
    "google_trends_kr": "구글 트렌드(다음 대체)",
    "naver_news_rank": "네이버 뉴스 랭킹(클립 대체)",
}

KST = timezone(timedelta(hours=9))


def _item_key(item: dict) -> str:
    return f"{item['source']}:{item['keyword']}"


def build_full_list_text(raw_items: list[dict], seen_keys: set[str], now: datetime) -> str:
    lines = [f"📋 [{now.strftime('%m/%d %H:%M')}] 실시간 트렌드 전체 목록"]
    by_source: dict[str, list[dict]] = {}
    for item in raw_items:
        by_source.setdefault(item["source"], []).append(item)

    for source, label in SOURCE_LABELS.items():
        items = by_source.get(source, [])
        if not items:
            continue
        lines.append(f"\n[{label}]")
        for item in items:
            new_mark = " 🆕새로 진입" if _item_key(item) not in seen_keys else ""
            lines.append(f"{item['rank']}. {item['keyword']}{new_mark}")

    return "\n".join(lines)


def build_card_text(candidate: dict) -> str:
    label = SOURCE_LABELS.get(candidate["source"], candidate["source"])
    return (
        f"🔥 {candidate['topic']}\n"
        f"출처: {label} #{candidate['rank']}\n\n"
        f"💡 연결 이유: {candidate.get('reason', '-')}\n"
        f"🎯 콘텐츠 각도: {candidate.get('angle', '-')}\n\n"
        f"추천: {candidate.get('suggested_action', 'blog')}"
    )


def _send_candidates(candidates: list[dict], now: datetime) -> int:
    """후보 카드를 발송하고 pending 상태에 기록한다. 발송 건수를 반환한다."""
    pending = state.load_pending()
    existing_ids = set(pending.get("candidates", {}).keys())

    sent = 0
    for c in candidates:
        if c["id"] in existing_ids:
            # 이미 대기 중이거나 처리된 후보는 중복 발송하지 않음
            continue
        text = build_card_text(c)
        try:
            message_id = telegram_api.send_candidate_card(c["id"], text)
        except Exception as e:
            print(f"[경고] 텔레그램 발송 실패 ({c['topic']}): {e}")
            continue
        c["status"] = "pending"
        c["message_id"] = message_id
        c["created_at"] = now.isoformat()
        pending.setdefault("candidates", {})[c["id"]] = c
        sent += 1

    state.save_pending(pending)
    return sent


def main():
    now = datetime.now(KST)

    # 임시: 다른 작업(OpenMontage 레퍼런스 분석 등)의 결과를 토큰 없이 텔레그램으로
    # 보고하고 싶을 때 원문 그대로 발송하고 종료한다.
    raw_message = os.environ.get("RAW_MESSAGE_TEXT", "").strip()
    if raw_message:
        print("[원문 전송 모드] 텔레그램으로 그대로 발송")
        telegram_api.send_long_text(raw_message)
        print("전송 완료")
        return

    # 테스트용: 실제 트렌드를 기다리지 않고 버튼 승인 흐름만 바로 확인하고 싶을 때.
    test_topic = os.environ.get("TEST_CANDIDATE_TOPIC", "").strip()
    if test_topic:
        print(f"[테스트 모드] 강제 후보 카드 발송: {test_topic}")
        cid = hashlib.md5(f"test:{test_topic}".encode("utf-8")).hexdigest()[:10]
        test_candidate = {
            "id": cid,
            "topic": test_topic,
            "source": "manual_test",
            "rank": 0,
            "reason": "수동 테스트용으로 강제 생성된 후보입니다.",
            "angle": "버튼 동작(글 발행/숏폼 제작/둘 다/넘김) 확인용.",
            "suggested_action": "both",
        }
        sent = _send_candidates([test_candidate], now)
        print(f"테스트 카드 {sent}건 발송 완료")
        return

    print(f"[{now.isoformat()}] 키워드 수집 시작")

    raw_items = sources.collect_all()
    print(f"원시 키워드 {len(raw_items)}개 수집")
    if not raw_items:
        print("수집된 키워드가 없어 종료합니다.")
        return

    # 1) 전체 목록 발송 (새로 진입 표시)
    seen_keys = state.load_seen_keywords()
    full_list_text = build_full_list_text(raw_items, seen_keys, now)
    try:
        telegram_api.send_long_text(full_list_text)
        print("전체 목록 발송 완료")
    except Exception as e:
        print(f"[경고] 전체 목록 발송 실패: {e}")

    state.save_seen_keywords({_item_key(item) for item in raw_items})

    # 2) 관련성 필터링 (시간당 최대 MAX_CANDIDATES_PER_RUN건, 적합한 게 없으면 스킵)
    candidates = relevance.filter_candidates(raw_items)[:MAX_CANDIDATES_PER_RUN]
    print(f"관련성 필터 통과: {len(candidates)}개")

    # 3) 통과한 키워드는 승인 여부와 무관하게 일별로 누적 저장
    keyword_storage.append_candidates(now.strftime("%Y-%m-%d"), now.isoformat(), candidates)

    if not candidates:
        print("적합한 주제가 없어 후보 카드를 보내지 않습니다.")
        return

    sent = _send_candidates(candidates, now)
    print(f"후보 카드 {sent}건 발송 완료")


if __name__ == "__main__":
    main()
