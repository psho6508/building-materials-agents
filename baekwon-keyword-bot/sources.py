"""4개 소스에서 실시간 트렌드 키워드를 수집한다.

각 함수는 [{"keyword": str, "rank": int, "source": str}, ...] 형태를 반환하며,
개별 소스 장애가 전체 수집을 막지 않도록 각자 예외를 흡수하고 빈 리스트를 반환한다.
"""

import re
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup

from config import REQUEST_HEADERS, REQUEST_TIMEOUT, SOURCE_LIMITS


def _get(url: str) -> requests.Response:
    resp = requests.get(url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp


def collect_nate_issue() -> list[dict]:
    """네이트 실시간 이슈 키워드 (nate.com 메인)."""
    try:
        resp = _get("https://www.nate.com/")
        soup = BeautifulSoup(resp.text, "html.parser")
        ol = soup.select_one("ol#olLiveIssueKeyword")
        items = []
        if ol:
            for li in ol.select("li"):
                rank_el = li.select_one(".num_rank")
                kw_el = li.select_one(".txt_rank")
                if rank_el and kw_el:
                    items.append(
                        {
                            "keyword": kw_el.get_text(strip=True),
                            "rank": int(rank_el.get_text(strip=True)),
                            "source": "nate_issue",
                        }
                    )
        return items[: SOURCE_LIMITS["nate_issue"]]
    except Exception as e:
        print(f"[경고] 네이트 수집 실패: {e}")
        return []


def collect_zum_ai_trend() -> list[dict]:
    """줌 AI 이슈트렌드 (zum.com 메인)."""
    try:
        resp = _get("https://www.zum.com/")
        soup = BeautifulSoup(resp.text, "html.parser")
        items = []
        for li in soup.select("li.issue-word-list__keyword-item"):
            rank_el = li.select_one(".issue-word-list__rank")
            kw_el = li.select_one(".issue-word-list__keyword")
            if rank_el and kw_el:
                items.append(
                    {
                        "keyword": kw_el.get_text(strip=True),
                        "rank": int(rank_el.get_text(strip=True)),
                        "source": "zum_ai_trend",
                    }
                )
        return items[: SOURCE_LIMITS["zum_ai_trend"]]
    except Exception as e:
        print(f"[경고] 줌 수집 실패: {e}")
        return []


def collect_google_trends_kr() -> list[dict]:
    """구글 트렌드 한국 실시간 급상승 검색어 (공식 RSS, 다음 실시간 트렌드 대체)."""
    try:
        resp = _get("https://trends.google.com/trending/rss?geo=KR")
        root = ET.fromstring(resp.content)
        items = []
        for i, item in enumerate(root.findall(".//item"), start=1):
            title_el = item.find("title")
            if title_el is not None and title_el.text:
                items.append(
                    {
                        "keyword": title_el.text.strip(),
                        "rank": i,
                        "source": "google_trends_kr",
                    }
                )
        return items[: SOURCE_LIMITS["google_trends_kr"]]
    except Exception as e:
        print(f"[경고] 구글 트렌드 수집 실패: {e}")
        return []


def collect_naver_news_rank() -> list[dict]:
    """네이버 뉴스 랭킹 — 언론사별 1위 기사 제목 (네이버 클립 대체)."""
    try:
        resp = _get("https://news.naver.com/main/ranking/popularDay.naver")
        soup = BeautifulSoup(resp.text, "html.parser")
        items = []
        rank = 1
        for box in soup.select("div.rankingnews_box"):
            title_el = box.select_one("ul.rankingnews_list li .list_content a.list_title")
            if title_el:
                title = re.sub(r"\s+", " ", title_el.get_text(strip=True))
                items.append(
                    {"keyword": title, "rank": rank, "source": "naver_news_rank"}
                )
                rank += 1
            if rank > SOURCE_LIMITS["naver_news_rank"]:
                break
        return items[: SOURCE_LIMITS["naver_news_rank"]]
    except Exception as e:
        print(f"[경고] 네이버 뉴스 랭킹 수집 실패: {e}")
        return []


def collect_all() -> list[dict]:
    """4개 소스를 모두 수집하여 하나의 리스트로 합친다."""
    all_items = []
    all_items += collect_nate_issue()
    all_items += collect_zum_ai_trend()
    all_items += collect_google_trends_kr()
    all_items += collect_naver_news_rank()
    return all_items
