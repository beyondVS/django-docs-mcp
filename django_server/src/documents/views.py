import time

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from documents.models import Document
from documents.services.search import get_search_service


async def playground(request: HttpRequest) -> HttpResponse:
    """
    검색 실험실(Playground)의 메인 화면을 렌더링합니다.

    DB에 등록된 고유한 Django 버전 및 카테고리 목록을 추출하여
    필터링 옵션으로 제공합니다.

    Args:
        request (HttpRequest): Django 요청 객체.

    Returns:
        HttpResponse: Playground 메인 페이지 템플릿 응답.
    """
    # 필터링을 위한 고유 버전 및 카테고리 목록 조회 (비동기 처리)
    versions = []
    async for v in Document.objects.values_list("target_version", flat=True).distinct():
        versions.append(v)

    categories = []
    async for c in Document.objects.values_list("category", flat=True).distinct():
        categories.append(c)

    context = {
        "versions": sorted(versions),
        "categories": sorted(categories),
    }
    return render(request, "playground/playground.html", context)


@require_GET
async def search_results(request: HttpRequest) -> HttpResponse:
    """
    HTMX를 통해 호출되는 검색 결과 엔드포인트입니다.

    사용자의 질의어와 필터 옵션을 바탕으로 SearchService를 호출하고,
    검색 결과 조각(Fragment)을 반환합니다.

    Args:
        request (HttpRequest): GET 인자로 q, version, category를 포함하는 요청 객체.

    Returns:
        HttpResponse: 검색 결과 리스트 템플릿 조각.
    """
    query = request.GET.get("q", "").strip()
    target_version = request.GET.get("version", "")
    category = request.GET.get("category", "")

    # 질의어가 없을 경우 빈 결과 반환
    if not query:
        return render(request, "playground/results.html", {"results": []})

    # 검색 서비스 호출
    search_service = get_search_service()

    start_time = time.time()
    results = await search_service.search(
        query=query,
        target_version=target_version if target_version != "All" else None,
        category=category if category != "All" else None,
        limit=5,
    )
    end_time = time.time()
    latency_ms = round((end_time - start_time) * 1000, 2)

    context = {
        "results": results,
        "query": query,
        "latency_ms": latency_ms,
    }
    return render(request, "playground/results.html", context)
