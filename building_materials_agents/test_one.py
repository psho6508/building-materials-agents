"""단일 에이전트 테스트 스크립트.

site_manager_crm 에이전트 1개만 실행하여
SDK 연결, 프롬프트, 파싱이 정상 동작하는지 확인한다.

사용법:
  python building_materials_agents/test_one.py

결과는 building_materials_agents/test_one_result.txt 에 저장됩니다.
"""

import json
import os
import sys
import traceback
from pathlib import Path

# Windows cp949 인코딩 문제 방지
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Claude Code 중첩 세션 방지
os.environ.pop("CLAUDECODE", None)

# 프로젝트 루트를 sys.path에 추가
PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))

# SDK monkey-patch 적용
from sdk_patch import apply_sdk_patches
apply_sdk_patches()

import anyio

# 파일 로거 (SDK가 stdout을 가져가도 결과를 볼 수 있도록)
LOG_PATH = PROJECT_DIR / "test_one_result.txt"
_log_file = open(LOG_PATH, "w", encoding="utf-8")

def log(msg):
    """stdout + 파일 동시 출력."""
    _log_file.write(msg + "\n")
    _log_file.flush()
    try:
        print(msg, flush=True)
    except Exception:
        pass


async def test_one_agent():
    """site_manager_crm 에이전트 1개만 테스트."""
    log("=" * 50)
    log("단일 에이전트 테스트 (site_manager_crm)")
    log("=" * 50)

    # Step 1: import 확인
    log("\n[1/4] import 확인...")
    try:
        from config import DATA_DIR, MODEL, MAX_TURNS, CRM_CSV_FILENAME
        log(f"  OK: config (MODEL={MODEL}, MAX_TURNS={MAX_TURNS})")
        log(f"  OK: CRM_CSV_FILENAME={CRM_CSV_FILENAME}")
    except ImportError as e:
        log(f"  FAIL: config import 실패 - {e}")
        return

    try:
        from agents.site_manager_crm import SiteManagerCRMAgent
        log("  OK: SiteManagerCRMAgent")
    except ImportError as e:
        log(f"  FAIL: SiteManagerCRMAgent import 실패 - {e}")
        return

    # Step 2: 데이터 파일 확인
    log("\n[2/4] 데이터 파일 확인...")
    csv_path = DATA_DIR / CRM_CSV_FILENAME
    if csv_path.exists():
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            lines = f.readlines()
        log(f"  OK: {csv_path.name} (행 수: {len(lines) - 1})")
    else:
        log(f"  FAIL: {csv_path} 파일 없음")
        return

    products_path = DATA_DIR / "products.json"
    if products_path.exists():
        with open(products_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        count = len(data) if isinstance(data, list) else len(data.get("products", data))
        log(f"  OK: products.json (항목 수: {count})")
    else:
        log(f"  FAIL: {products_path} 파일 없음")
        return

    # Step 3: Claude CLI 확인
    log("\n[3/4] Claude CLI 확인...")
    import shutil
    claude_path = shutil.which("claude")
    if claude_path:
        log(f"  OK: {claude_path}")
    else:
        log("  FAIL: claude CLI를 찾을 수 없습니다")
        return

    # Step 4: 에이전트 실행 (anyio.move_on_after로 타임아웃)
    log("\n[4/4] site_manager_crm 에이전트 실행 (타임아웃 600초)...")
    agent = SiteManagerCRMAgent()
    result = None
    try:
        with anyio.move_on_after(600) as cancel_scope:
            result = await agent.run()
        if cancel_scope.cancelled_caught:
            log("\n  TIMEOUT: 600초 초과 - 에이전트가 응답하지 않습니다")
        elif result is not None:
            log("\n  OK: 에이전트 실행 완료!")
            log("\n--- 결과 ---")
            log(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            log("\n  WARN: 에이전트가 None을 반환했습니다")
    except Exception as e:
        log(f"\n  FAIL: 에이전트 실행 에러 - {type(e).__name__}: {e}")
        log(traceback.format_exc())

    log("\n=== 테스트 종료 ===")


if __name__ == "__main__":
    try:
        anyio.run(test_one_agent)
    except Exception as e:
        log(f"최상위 에러: {type(e).__name__}: {e}")
        log(traceback.format_exc())
    finally:
        _log_file.close()
        try:
            print(f"\n결과 저장: {LOG_PATH}", flush=True)
        except Exception:
            pass
