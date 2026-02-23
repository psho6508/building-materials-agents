"""Agent 3: 소장 CRM 에이전트 — 563명 실데이터 기반 착공 매칭 + 기존고객/신규개척 판단."""

import json

import anyio

from .base import BaseAgent
from config import CRM_CSV_FILENAME, CRM_GRADE_PRIORITY

SYSTEM_PROMPT = (
    "당신은 건축자재 유통업체(백원철물건재)의 현장소장 CRM 전문가입니다. "
    "건설회사_소장 데이터.csv 563명 실데이터를 기반으로 분석합니다. "
    "CSV 컬럼: 이름,구분(등급),담당자,만난현장,부서/직위,연락처,주소,최신근황,통화및방문날짜,회사명,건축현황. "
    "등급 분류: HOT(최우선)>HIGH WARM>LOW WARM>COLD>COLD-L>COLD-D. "
    "분석 프로세스: "
    "1) WebSearch로 서울/경기 최근 착공 현장 정보를 검색한다. "
    "2) 검색된 착공 현장의 건설사명을 CSV DB의 회사명 컬럼과 매칭한다. "
    "3) 매칭 성공=기존고객: 과거 거래 이력(만난현장,최신근황) 활용하여 즉시 전화 스크립트 작성. "
    "4) 매칭 실패=신규개척: 콜드콜 메시지 생성, DO/HOLD 판단. "
    "5) 등급별 우선순위로 정렬하여 파이프라인 리포트 작성. "
    "예상매출 추정: 착공 규모 기반 자재 소요량 x 자재 단가(products.json). "
    "DO 판단: HOT/HIGH WARM 등급 기존고객 또는 대형 착공 신규개척. "
    "HOLD 판단: LOW WARM 이하 등급 또는 소규모 현장. "
    "반드시 JSON으로만 응답하세요. 코드블록(```)없이 순수 JSON만 출력하세요."
)


class SiteManagerCRMAgent(BaseAgent):
    """소장 CRM 에이전트 — 563명 실데이터 기반."""

    name = "site_manager_crm"
    description = "소장 CRM (563명 실데이터)"
    SYSTEM_PROMPT = SYSTEM_PROMPT
    allowed_tools = ["WebSearch", "Read"]
    fallback_result = {
        "agent": "site_manager_crm",
        "matched_opportunities": [],
        "new_prospects": [],
    }

    def build_prompt(self, **kwargs) -> str:
        """에이전트 프롬프트 생성: CSV DB 매칭 + 기존고객/신규개척 분류."""
        csv_path = self._data_path(CRM_CSV_FILENAME)
        products_path = self._data_path("products.json")
        today = self.today()

        grade_desc = ", ".join(
            f"{g}(우선순위{p})" for g, p in CRM_GRADE_PRIORITY.items()
        )

        return (
            f"오늘은 {today}입니다. "
            f"Read로 소장 DB CSV를 읽으세요: {csv_path} . "
            f"Read로 자재 카탈로그를 읽으세요: {products_path} . "
            'WebSearch로 "서울 경기 건축 착공 현장 2026"을 검색하세요. '
            "분석 순서: "
            "1) CSV 파일에서 전체 소장 수, 등급별 분포(HOT/HIGH WARM/LOW WARM/COLD/COLD-L/COLD-D)를 집계하세요. "
            "2) 웹 검색 결과에서 착공 현장의 건설사명을 추출하세요. "
            "3) 추출한 건설사명을 CSV의 회사명 컬럼과 매칭하세요(부분 일치 포함). "
            "4) 매칭 성공한 소장은 기존고객(matched_opportunities)으로: "
            "이름, 회사명, 등급, 연락처, 담당자, 착공현장정보, 최신근황, "
            "자재카탈로그 기반 예상매출/수익, 전화 스크립트, DO/HOLD 판단을 포함하세요. "
            "5) 매칭 실패한 건설사는 신규개척(new_prospects)으로: "
            "건설사명, 착공현장정보, 콜드콜 메시지, DO/HOLD 판단을 포함하세요. "
            "6) pipeline_summary에 기존고객/신규개척 건수, 매출합산, 번들매출을 집계하세요. "
            "7) priority_actions에 오늘 즉시 해야 할 일 목록을 작성하세요. "
            f"등급 우선순위: {grade_desc}. "
            "JSON 형식: "
            f'{{"agent":"site_manager_crm","timestamp":"{today}",'
            '"db_stats":{"total_contacts":563,"hot":0,"high_warm":0,"low_warm":0,"cold":0,"cold_l":0,"cold_d":0},'
            '"matched_opportunities":[{"type":"기존고객","manager_name":"소장명","company":"회사명",'
            '"grade":"등급","phone":"연락처","rep":"담당자","site_info":"착공현장정보",'
            '"latest_status":"최신근황","estimated_revenue":0,"estimated_profit":0,'
            '"contact_message":"전화 스크립트","decision":"DO","decision_reason":"판단 근거"}],'
            '"new_prospects":[{"type":"신규개척","company":"건설사명","site_info":"착공현장정보",'
            '"cold_call_message":"콜드콜 메시지","decision":"DO","decision_reason":"판단 근거"}],'
            '"pipeline_summary":{"existing_customers_count":0,"existing_customers_revenue":0,'
            '"new_prospects_count":0,"new_prospects_revenue":0,"total_pipeline_revenue":0,"bundle_revenue":0},'
            '"priority_actions":["오늘 즉시 할 일"],"summary":"요약"}'
        )


async def main():
    """단독 실행용."""
    agent = SiteManagerCRMAgent()
    result = await agent.run()
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    anyio.run(main)
