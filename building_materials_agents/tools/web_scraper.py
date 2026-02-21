"""웹 스크래핑 도구.

나라장터 입찰공고, 철강/시멘트 시세 등을 검색하기 위한 헬퍼.
실제 구현에서는 WebSearch/WebFetch 도구를 Claude Agent가 직접 사용하며,
이 모듈은 검색 쿼리 생성 및 결과 파싱을 보조한다.
"""


def build_bid_search_query(region: str = "서울", material_type: str = "") -> str:
    """나라장터/세움터 입찰공고 검색 쿼리 생성."""
    base = f"나라장터 입찰공고 건축자재 {region} 2026"
    if material_type:
        base += f" {material_type}"
    return base


def build_price_search_query(material: str) -> str:
    """자재 시세 검색 쿼리 생성."""
    return f"{material} 시세 가격 동향 2026년 2월"


def search_bids(region: str = "서울") -> str:
    """입찰공고 검색을 위한 쿼리 반환 (에이전트가 WebSearch로 실행)."""
    return build_bid_search_query(region)


def search_price_info(material: str) -> str:
    """자재 시세 검색을 위한 쿼리 반환 (에이전트가 WebSearch로 실행)."""
    return build_price_search_query(material)
