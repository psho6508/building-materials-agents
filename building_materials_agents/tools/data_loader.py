"""JSON 데이터 로더.

data/ 디렉토리의 JSON 파일들을 로드하여 에이전트에 제공한다.
"""

import json
from pathlib import Path

from config import DATA_DIR


def load_json(filename: str) -> list[dict]:
    """JSON 파일을 로드하여 리스트로 반환."""
    filepath = DATA_DIR / filename
    if not filepath.exists():
        return []
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def load_site_managers() -> list[dict]:
    """소장 네트워크 데이터를 로드."""
    return load_json("site_managers.json")


def load_products() -> list[dict]:
    """자재 카탈로그를 로드."""
    return load_json("products.json")


def load_fixman_reports() -> list[dict]:
    """픽스맨 점검 리포트를 로드."""
    return load_json("fixman_reports.json")


def get_products_by_category(category: str) -> list[dict]:
    """카테고리별 자재 필터링."""
    products = load_products()
    return [p for p in products if p["category"] == category]


def get_price_alert_products(threshold_pct: float = 3.0) -> list[dict]:
    """가격 변동이 임계값 이상인 자재 목록."""
    products = load_products()
    return [
        p for p in products
        if abs(p["price_change_pct"]) >= threshold_pct
    ]


def get_urgent_fixman_items() -> list[dict]:
    """긴급 점검 항목만 추출."""
    reports = load_fixman_reports()
    urgent_items = []
    for report in reports:
        for item in report["items"]:
            if item["urgency"] == "긴급":
                urgent_items.append({
                    "site_name": report["site_name"],
                    "contact_person": report["contact_person"],
                    "contact_phone": report["contact_phone"],
                    **item,
                })
    return urgent_items


def get_managers_needing_contact(days_threshold: int = 7) -> list[dict]:
    """최근 연락이 일정 기간 이상 지난 소장 목록."""
    from datetime import date, timedelta

    managers = load_site_managers()
    cutoff = date.today() - timedelta(days=days_threshold)
    return [
        m for m in managers
        if date.fromisoformat(m["last_contact"]) <= cutoff
    ]
