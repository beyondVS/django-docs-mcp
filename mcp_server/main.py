import os
import sys
from pathlib import Path

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

import django  # noqa: E402

django.setup()

# MCP 서버 초기화
mcp = FastMCP("Django Docs Search")

# 세션 내 최근 검색어 추적 (중복 경고용)
_recent_queries: set[str] = set()


@mcp.tool()
async def search_django_docs(query: str, django_version: str = "5.2", max_results: int = 5) -> str:
    """
    Django 공식 문서를 하이브리드 검색(Vector + BM25) 및 리랭킹(MaxSim)을 통해 검색합니다.

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
    results = await search_service.search(
        query=query, target_version=django_version, limit=max_results
    )

    # 상세 로깅 (US2 & 헌법 V.3 준수)
    log_tool_call(
        tool_name="search_django_docs",
        query=query,
        results=results,
        params={"django_version": django_version, "max_results": max_results},
    )

    if not results:
        return f"No results found for query: '{query}'. Try using different keywords."

    formatted_results = []
    for i, res in enumerate(results, 1):
        # res는 dict 형태 (score/similarity, document_title, content, extra_meta 등 포함)
        score = res.get("relevance_score") or res.get("similarity") or 0.0
        title = res.get("document_title") or "No Title"
        section = res.get("section_title") or ""
        content = res.get("content", "No Content")
        url = res.get("extra_meta", {}).get("source_url", "No URL")

        full_title = f"{title} > {section}" if section else title

        formatted_results.append(
            f"[Result {i}] (Score: {score:.4f})\n"
            f"Title: {full_title}\n"
            f"URL: {url}\n"
            f"Content:\n{content}\n"
            f"{'=' * 40}"
        )

    return "\n\n".join(formatted_results)


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
    mcp.run()
