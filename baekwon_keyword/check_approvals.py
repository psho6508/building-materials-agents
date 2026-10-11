"""텔레그램 버튼 콜백을 폴링하여 승인된 후보의 원고/대본을 생성한다.

GitHub Actions 워크플로우(baekwon-approval-check.yml)에서 10분 간격으로 호출된다.
완전한 실시간은 아니지만(최대 폴링 주기만큼 지연) 컴퓨터가 꺼져 있어도 동작한다.

버튼 단계:
1. 후보 카드: 📝 글 발행 / 🎬 숏폼 제작 / 🔀 둘 다 / ❌ 넘김 (status: pending → done/rejected/error)
2. 숏폼 대본이 나오면 별도 메시지로 승인 카드 발송: 🎬 영상 만들기 / ❌ 취소
   (video_status: script_ready → approved/cancelled)
   '영상 만들기'는 실제 제작을 시작하지 않는다 — OpenMontage는 에이전트가 단계별로
   직접 운전해야 하는 시스템이라 무인 자동화가 불가능하므로, 여기서는 '승인 대기열'에
   올리기만 하고 사람이 Claude Code 세션에서 직접 제작을 요청해야 한다.
각 단계는 해당 상태 필드로 중복 클릭을 막는다.
"""

from datetime import datetime, timezone, timedelta

import content_draft
import footage
import gdrive
import state
import telegram_api
from config import DRAFTS_DIR, GITHUB_BRANCH, GITHUB_REPOSITORY

KST = timezone(timedelta(hours=9))

INITIAL_ACTIONS = {"blog", "video", "both", "reject"}
VIDEO_APPROVAL_ACTIONS = {"mkvid", "cancelvid"}


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

    match = footage.find_matching_footage(candidate["topic"])
    if match:
        candidate["footage_folder_url"] = match["folder_url"]
        candidate["footage_folder_name"] = match["folder_name"]

    return (
        f"✅ 블로그 원고 완성 → 구글 드라이브 저장됨\n\n"
        f"📄 원고 보기: {url}\n\n"
        "※ 티스토리에는 사람이 수동으로 붙여넣기 후 발행해주세요 (공식 글쓰기 API가 "
        "폐지되어 자동 발행은 지원하지 않습니다)." + footage.format_footage_note(match)
    )


def _start_video_review(candidate: dict, date_str: str, cid: str):
    """영상 대본을 생성해 저장소에 커밋하고, 승인 버튼과 함께 별도 메시지로 보낸다."""
    draft_text = content_draft.generate_video_script(candidate)
    filename = f"{date_str}-{cid}.md"
    path = DRAFTS_DIR / "video" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(draft_text, encoding="utf-8")
    url = _video_draft_url(filename)
    candidate["video_script_url"] = url

    match = footage.find_matching_footage(candidate["topic"])
    if match:
        candidate["footage_folder_url"] = match["folder_url"]
        candidate["footage_folder_name"] = match["folder_name"]

    stripped = draft_text.strip()
    excerpt = stripped[:800] + ("..." if len(stripped) > 800 else "")
    text = (
        f"🎬 영상 대본 완성 — 승인하면 제작 대기열에 올라갑니다\n\n"
        f"{candidate['topic']}\n\n{excerpt}\n\n📄 전체 대본: {url}"
        + footage.format_footage_note(match)
    )
    candidate["video_message_id"] = telegram_api.send_video_review_card(cid, text)
    candidate["video_status"] = "script_ready"


def _handle_initial_action(candidate: dict, action: str, cid: str):
    message_id = candidate.get("message_id")
    topic = candidate["topic"]

    if action == "reject":
        candidate["status"] = "rejected"
        if message_id:
            telegram_api.edit_message(message_id, f"❌ 넘김\n\n{topic}")
        return

    busy_label = {"blog": "글", "video": "숏폼 대본", "both": "글+숏폼 대본"}[action]
    if message_id:
        telegram_api.edit_message(message_id, f"⏳ {busy_label} 생성 중...\n\n{topic}")

    date_str = datetime.now(KST).strftime("%Y-%m-%d")
    had_error = False
    blog_text = None

    if action in ("blog", "both"):
        try:
            blog_text = _make_blog(candidate, date_str)
        except Exception as e:
            had_error = True
            print(f"[경고] 블로그 원고 생성 실패 ({topic}): {e}")
            blog_text = f"⚠️ 블로그 원고 생성 실패: {e}"

    if action in ("video", "both"):
        try:
            _start_video_review(candidate, date_str, cid)
        except Exception as e:
            had_error = True
            print(f"[경고] 영상 대본 생성 실패 ({topic}): {e}")
            if message_id:
                telegram_api.send_text(f"⚠️ 영상 대본 생성 실패: {e}\n\n{topic}")

    candidate["status"] = "error" if had_error else "done"

    if blog_text and message_id:
        telegram_api.edit_message(message_id, f"{topic}\n\n{blog_text}")
    elif blog_text:
        telegram_api.send_text(f"{topic}\n\n{blog_text}")
    elif message_id and action == "video":
        telegram_api.edit_message(
            message_id, f"{topic}\n\n🎬 영상 대본을 아래 새 메시지로 보냈습니다. 확인 후 승인해주세요."
        )


def _handle_video_approval(candidate: dict, action: str):
    message_id = candidate.get("video_message_id")
    topic = candidate["topic"]

    if action == "cancelvid":
        candidate["video_status"] = "cancelled"
        if message_id:
            telegram_api.edit_message(message_id, f"❌ 영상 제작 취소됨\n\n{topic}")
        return

    candidate["video_status"] = "approved"
    if message_id:
        telegram_api.edit_message(
            message_id,
            f"✅ 영상 제작 승인됨 — 대기열에 등록\n\n{topic}\n\n"
            '다음에 Claude Code에서 "영상 제작 진행해줘"라고 말씀해주시면 '
            "OpenMontage로 실제 제작을 시작합니다.",
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

        if action in INITIAL_ACTIONS:
            if candidate.get("status") != "pending":
                telegram_api.answer_callback(cq_id, "이미 처리된 항목입니다")
                continue
            telegram_api.answer_callback(cq_id, "처리 중...")
            changed = True
            _handle_initial_action(candidate, action, cid)
            continue

        if action in VIDEO_APPROVAL_ACTIONS:
            if candidate.get("video_status") != "script_ready":
                telegram_api.answer_callback(cq_id, "이미 처리됐거나 대기 중인 대본이 아닙니다")
                continue
            telegram_api.answer_callback(cq_id, "처리 중...")
            changed = True
            _handle_video_approval(candidate, action)
            continue

    if changed:
        state.save_pending(pending)
    state.save_offset(max_update_id + 1)


if __name__ == "__main__":
    main()
