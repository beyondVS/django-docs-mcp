import os
import sys
from pathlib import Path
from typing import Literal

from fastmcp import FastMCP

# Django 프로젝트 경로 추가 (상위 디렉토리의 django_server/src)
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
DJANGO_SRC = PROJECT_ROOT / "django_server" / "src"

if str(DJANGO_SRC) not in sys.path:
    sys.path.append(str(DJANGO_SRC))

if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# Django 환경 변수 설정 및 초기화
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# MCP 서버 초기화
mcp = FastMCP("Django Docs Search")

# 세션 내 최근 검색어 추적 (중복 경고용)
_recent_queries: set[str] = set()


@mcp.tool(
    name="search_django_knowledge",
    timeout=5.0,
    annotations={
        "readOnlyHint": True,  # 데이터 변경이 없는 조회 전용임을 명시
        "idempotentHint": True,  # 동일 쿼리에 대해 일관된 결과를 보장
    },
)
async def search_django_knowledge(
    query: str,
    django_version: Literal["2.x", "4.2", "5.2"] | None = None,
    document_type: Literal["Documentation", "Cookbook"] | None = None,
    max_results: int = 5,
) -> list[dict]:
    """
    AI 에이전트가 Django 공식 가이드와 코드를 검색하기 위해 호출하는
    RAG 기반 하이브리드 검색(Vector + BM25 + Rerank) 도구입니다.

    ### 🚀 에이전틱 서치 지침 (Agentic Search Guide):
    1. **키워드 최적화**: 구체적이고 명확한 키워드를 사용하세요.
    2. **단계적 탐색**: 첫 번째 결과가 부족하면, 결과 내 새로운 개념이나 키워드로 재검색하세요.
    3. **중복 금지**: 🚫 동일한 검색어를 반복하지 마세요. (이미 시도한 쿼리는 다른 키워드로 변경)
    4. **품질 검증**: 리랭크 점수가 낮다면 검색어가 너무 모호할 수 있습니다.
       더 구체적인 키워드를 시도하세요.
    """

    from documents.services.search import get_search_service

    from mcp_server.logger import log_tool_call, logger

    # 중복 검색어 체크 (US3)
    is_duplicate = query in _recent_queries
    if is_duplicate:
        logger.warning(f"Duplicate query detected: {query}. Agent should optimize search strategy.")
    _recent_queries.add(query)

    search_service = get_search_service()

    # Django 하이브리드 검색 서비스 호출 (Async)
    # SearchService의 'category' 파라미터가 규약의 'document_type'에 대응함
    results = await search_service.search(
        query=query,
        target_version=django_version,
        category=document_type,
        limit=min(max_results, 10),  # 규약상 최대 10개 제한
    )

    # 상세 로깅 (US2 & 헌법 V.3 준수)
    log_tool_call(
        tool_name="search_django_knowledge",
        query=query,
        results=results,
        params={
            "django_version": django_version,
            "document_type": document_type,
            "max_results": max_results,
        },
    )

    # mcp_tools_contract.md 규격에 맞춘 결과 변환
    formatted_results = []
    for res in results:
        # SearchService 결과 필드 매핑
        extra_meta = res.get("extra_meta", {})
        formatted_results.append(
            {
                "content": res.get("content", ""),
                "target_version": res.get("version") or django_version,
                "document_type": extra_meta.get("category", "unknown"),
                "source_url": extra_meta.get("source_url", ""),
                "relevance_score": res.get("relevance_score") or res.get("similarity") or 0.0,
                "extra_meta": {
                    "document_title": res.get("document_title"),
                    "section_title": res.get("section_title"),
                    "id": res.get("id"),
                    **{k: v for k, v in extra_meta.items() if k not in ["source_url", "category"]},
                },
            }
        )

    return formatted_results


@mcp.tool()
async def test_django_connection() -> str:
    """Django 앱 레지스트리가 정상적으로 로드되었는지 확인합니다."""
    from django.apps import apps

    if apps.ready:
        loaded_apps = [app.label for app in apps.get_app_configs()]
        return f"Django is READY. Loaded apps: {', '.join(loaded_apps)}"
    return "Django is NOT ready."


if __name__ == "__main__":
    # MCP 서버 실행
    mcp.run(transport="sse", host="127.0.0.1", port=8080)
