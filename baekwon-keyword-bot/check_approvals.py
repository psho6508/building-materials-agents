"""텔레그램 버튼 콜백을 폴링하여 승인된 후보의 초안을 생성한다.

GitHub Actions 워크플로우(baekwon-approval-check.yml)에서 10분 간격으로 호출된다.
완전한 실시간은 아니지만(최대 폴링 주기만큼 지연) 컴퓨터가 꺼져 있어도 동작한다.
"""

from datetime import datetime, timezone, timedelta

import content_draft
import state
import telegram_api
from config import DRAFTS_DIR, GITHUB_BRANCH, GITHUB_REPOSITORY

KST = timezone(timedelta(hours=9))

ACTION_LABELS = {"blog": "블로그 초안", "video": "영상 대본"}


def _draft_url(action: str, filename: str) -> str:
    subdir = "blog" if action == "blog" else "video"
    return (
        f"https://github.com/{GITHUB_REPOSITORY}/blob/{GITHUB_BRANCH}/"
        f"baekwon-keyword-bot/drafts/{subdir}/{filename}"
    )


def main():
    pending = state.load_pending()
    candidates = pending.setdefault("candidates", {})
    offset = state.load_offset()

    updates = telegram_api.get_updates(offset)
    print(f"업데이트 {len(updates)}건 수신 (offset={offset})")

    max_update_id = offset - 1
    changed = False

    for update in updates:
        max_update_id = max(max_update_id, update["update_id"])
        cq = update.get("callback_query")
        if not cq or "data" not in cq:
            continue

        data = cq["data"]
        cq_id = cq["id"]
        if ":" not in data:
            continue
        action, cid = data.split(":", 1)

        candidate = candidates.get(cid)
        if not candidate:
            telegram_api.answer_callback(cq_id, "후보를 찾을 수 없습니다 (만료됨)")
            continue
        if candidate.get("status") != "pending":
            telegram_api.answer_callback(cq_id, "이미 처리된 항목입니다")
            continue

        telegram_api.answer_callback(cq_id, "처리 중...")
        message_id = candidate.get("message_id")
        changed = True

        if action == "reject":
            candidate["status"] = "rejected"
            if message_id:
                telegram_api.edit_message(message_id, f"❌ 거절됨\n\n{candidate['topic']}")
            continue

        if action not in ("blog", "video"):
            continue

        label = ACTION_LABELS[action]
        if message_id:
            telegram_api.edit_message(
                message_id, f"⏳ {label} 생성 중...\n\n{candidate['topic']}"
            )

        try:
            draft_text = (
                content_draft.generate_blog_draft(candidate)
                if action == "blog"
                else content_draft.generate_video_script(candidate)
            )
        except Exception as e:
            candidate["status"] = "error"
            print(f"[경고] 초안 생성 실패 ({candidate['topic']}): {e}")
            if message_id:
                telegram_api.edit_message(
                    message_id, f"⚠️ 생성 실패: {e}\n\n{candidate['topic']}"
                )
            continue

        date_str = datetime.now(KST).strftime("%Y-%m-%d")
        filename = f"{date_str}-{cid}.md"
        subdir = "blog" if action == "blog" else "video"
        path = DRAFTS_DIR / subdir / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(draft_text, encoding="utf-8")

        url = _draft_url(action, filename)
        candidate["status"] = "done"
        candidate["result_url"] = url

        excerpt = draft_text.strip()[:300]
        result_text = (
            f"✅ {label} 완성\n\n{candidate['topic']}\n\n{excerpt}...\n\n"
            f"📄 전체 초안: {url}\n\n"
            "※ 실제 발행/업로드는 직접 진행해주세요 (네이버 공식 글쓰기 API, "
            "유튜브 업로드 인증이 없어 자동 발행은 지원하지 않습니다)."
        )
        if message_id:
            telegram_api.edit_message(message_id, result_text)
        else:
            telegram_api.send_text(result_text)

    if changed:
        state.save_pending(pending)
    state.save_offset(max_update_id + 1)


if __name__ == "__main__":
    main()
