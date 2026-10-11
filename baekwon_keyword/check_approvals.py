"""텔레그램 버튼 콜백을 폴링하여 승인된 후보의 원고/대본을 생성한다.

GitHub Actions 워크플로우(baekwon-approval-check.yml)에서 10분 간격으로 호출된다.
완전한 실시간은 아니지만(최대 폴링 주기만큼 지연) 컴퓨터가 꺼져 있어도 동작한다.

버튼: 📝 글 발행 / 🎬 숏폼 제작 / 🔀 둘 다 / ❌ 넘김.
후보 상태(pending → done/rejected/error)로 중복 클릭을 막는다.
"""

from datetime import datetime, timezone, timedelta

import content_draft
import gdrive
import state
import telegram_api
from config import DRAFTS_DIR, GITHUB_BRANCH, GITHUB_REPOSITORY

KST = timezone(timedelta(hours=9))


def _video_draft_url(filename: str) -> str:
    return (
        f"https://github.com/{GITHUB_REPOSITORY}/blob/{GITHUB_BRANCH}/"
        f"baekwon_keyword/drafts/video/{filename}"
    )


def _make_blog(candidate: dict, date_str: str) -> str:
    """블로그 원고를 생성해 구글 드라이브에 저장하고, 결과 메시지를 반환한다."""
    draft_text = content_draft.generate_blog_draft(candidate)
    doc_title = f"{date_str}_{candidate['topic'][:40]}"
    url = gdrive.upload_manuscript(doc_title, draft_text)
    candidate["blog_result_url"] = url
    return (
        f"✅ 블로그 원고 완성 → 구글 드라이브 저장됨\n\n"
        f"📄 원고 보기: {url}\n\n"
        "※ 사진/영상은 '집수리 현장 사진 및 영상' 폴더에서 골라 직접 넣고, "
        "티스토리에 붙여넣기 후 발행해주세요 (티스토리는 공식 글쓰기 API가 없어 "
        "자동 발행은 지원하지 않습니다)."
    )


def _make_video(candidate: dict, date_str: str, cid: str) -> str:
    """영상 대본을 생성해 저장소에 커밋하고, 결과 메시지를 반환한다."""
    draft_text = content_draft.generate_video_script(candidate)
    filename = f"{date_str}-{cid}.md"
    path = DRAFTS_DIR / "video" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(draft_text, encoding="utf-8")
    url = _video_draft_url(filename)
    candidate["video_result_url"] = url
    excerpt = draft_text.strip()[:300]
    return (
        f"✅ 영상 대본 완성\n\n{excerpt}...\n\n"
        f"📄 전체 대본: {url}\n\n"
        "※ 유튜브 업로드 인증이 없어 자동 업로드는 지원하지 않습니다. "
        "대본 확인 후 직접 제작/업로드해주세요."
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
        topic = candidate["topic"]

        if action == "reject":
            candidate["status"] = "rejected"
            if message_id:
                telegram_api.edit_message(message_id, f"❌ 넘김\n\n{topic}")
            continue

        if action not in ("blog", "video", "both"):
            continue

        busy_label = {"blog": "글", "video": "숏폼 대본", "both": "글+숏폼 대본"}[action]
        if message_id:
            telegram_api.edit_message(message_id, f"⏳ {busy_label} 생성 중...\n\n{topic}")

        date_str = datetime.now(KST).strftime("%Y-%m-%d")
        parts = []
        had_error = False

        if action in ("blog", "both"):
            try:
                parts.append(_make_blog(candidate, date_str))
            except Exception as e:
                had_error = True
                print(f"[경고] 블로그 원고 생성 실패 ({topic}): {e}")
                parts.append(f"⚠️ 블로그 원고 생성 실패: {e}")

        if action in ("video", "both"):
            try:
                parts.append(_make_video(candidate, date_str, cid))
            except Exception as e:
                had_error = True
                print(f"[경고] 영상 대본 생성 실패 ({topic}): {e}")
                parts.append(f"⚠️ 영상 대본 생성 실패: {e}")

        candidate["status"] = "error" if had_error else "done"
        result_text = f"{topic}\n\n" + "\n\n".join(parts)

        if message_id:
            telegram_api.edit_message(message_id, result_text)
        else:
            telegram_api.send_text(result_text)

    if changed:
        state.save_pending(pending)
    state.save_offset(max_update_id + 1)


if __name__ == "__main__":
    main()
