"""하루 4회 실행: 4개 소스 수집 → 관련성 필터링 → 텔레그램 후보 카드 발송.

GitHub Actions 워크플로우(baekwon-keyword-collect.yml)에서 호출된다.
"""

from datetime import datetime, timezone, timedelta

import relevance
import sources
import state
import telegram_api

SOURCE_LABELS = {
    "nate_issue": "네이트 실시간 이슈",
    "zum_ai_trend": "줌 AI 이슈트렌드",
    "google_trends_kr": "구글 트렌드(다음 대체)",
    "naver_news_rank": "네이버 뉴스 랭킹(클립 대체)",
}

KST = timezone(timedelta(hours=9))


def build_card_text(candidate: dict) -> str:
    label = SOURCE_LABELS.get(candidate["source"], candidate["source"])
    return (
        f"🔥 <b>{candidate['topic']}</b>\n"
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

    candidates = relevance.filter_candidates(raw_items)
    print(f"관련성 필터 통과: {len(candidates)}개")

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
    print(f"텔레그램 카드 {sent}건 발송 완료")

    if sent == 0:
        try:
            telegram_api.send_text(
                f"ℹ️ [{now.strftime('%m/%d %H:%M')}] 이번 수집에서 새로운 관련 주제를 찾지 못했습니다."
            )
        except Exception as e:
            print(f"[경고] 안내 메시지 발송 실패: {e}")


if __name__ == "__main__":
    main()
