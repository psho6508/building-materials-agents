"""하루 4회 실행: 4개 소스 수집 → 전체 목록 발송 → 관련성 필터링 → 후보 카드 발송.

GitHub Actions 워크플로우(baekwon-keyword-collect.yml)에서 호출된다.
"""

from datetime import datetime, timezone, timedelta

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


def main():
    now = datetime.now(KST)
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

    if not candidates:
        print("적합한 주제가 없어 후보 카드를 보내지 않습니다.")
        return

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
    print(f"후보 카드 {sent}건 발송 완료")


if __name__ == "__main__":
    main()
