"""키워드와 매칭되는 집수리 현장 사진/영상을 구글 드라이브에서 찾는다.

프로세스: (1) 폴더명과 주제를 비교해 같은 현장인지 확인 → (2) 있으면 그 폴더의
파일 목록을 가져와 결과에 붙임 → (3) 없으면 그냥 넘어간다. 실패해도 전체 흐름을
막지 않도록 예외를 흡수하고 None을 반환한다.
"""

from anthropic import Anthropic

from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL, APPS_SCRIPT_URL, GDRIVE_FOOTAGE_FOLDER_ID
from gdrive import call_apps_script


def _pick_best_folder(topic: str, folders: list[dict]) -> dict | None:
    if not folders:
        return None

    names = "\n".join(f"{i+1}. {f['name']}" for i, f in enumerate(folders))
    prompt = (
        f"아래는 실제로 진행된 집수리 현장 작업 폴더 목록입니다:\n{names}\n\n"
        f"이 중 아래 주제와 '같은 현장/같은 작업'이라고 볼 수 있을 만큼 명확히 일치하는 "
        "폴더가 있으면 그 번호만 답하세요. 비슷해 보여도 억지로 끼워맞추는 수준이면 0을 "
        f"답하세요.\n주제: {topic}\n\n숫자 하나만 답하세요 (설명 없이)."
    )
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=50,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(b.text for b in message.content if hasattr(b, "text")).strip()
    print(
        f"[현장자료매칭] 폴더 {len(folders)}개, stop_reason={message.stop_reason}, "
        f"content={message.content!r}, 응답텍스트={text!r}"
    )
    digits = "".join(ch for ch in text if ch.isdigit())
    if not digits:
        return None
    idx = int(digits)
    if idx <= 0 or idx > len(folders):
        return None
    return folders[idx - 1]


def find_matching_footage(topic: str) -> dict | None:
    """매칭되는 현장 폴더가 있으면 {"folder_name","folder_url","files":[...]}, 없으면 None."""
    if not APPS_SCRIPT_URL or not ANTHROPIC_API_KEY:
        return None
    try:
        listing = call_apps_script("list_footage_folders", folderId=GDRIVE_FOOTAGE_FOLDER_ID)
        folders = listing.get("folders", [])
        print(f"[현장자료매칭] 조회된 폴더: {[f['name'] for f in folders]!r}")
        folder = _pick_best_folder(topic, folders)
        if not folder:
            return None
        files_data = call_apps_script("list_folder_files", folderId=folder["id"])
        return {
            "folder_name": folder["name"],
            "folder_url": folder["url"],
            "files": files_data.get("files", []),
        }
    except Exception as e:
        print(f"[경고] 현장 자료 매칭 실패(무시하고 진행): {e}")
        return None


def format_footage_note(match: dict | None) -> str:
    """텔레그램 메시지에 덧붙일 현장 자료 안내 문구. 매칭 없으면 빈 문자열."""
    if not match:
        return ""
    n = len(match["files"])
    return (
        f"\n\n📷 관련 현장 자료 발견: {match['folder_name']} (파일 {n}개)\n"
        f"{match['folder_url']}\n"
        "※ 실제 사진/영상을 써서 신뢰도를 높이세요."
    )
