import asyncio
import os
import sys
from pathlib import Path

import django

# Django 설정 로드 (import 이전에 수행되어야 함)
# src 디렉토리를 파이썬 경로에 추가
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR / "src"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

# ruff: noqa: E402 (Django setup 이후 임포트를 허용)
from documents.services.search import get_search_service

# US3: 골든 데이터셋 정의 (Django ORM Cookbook 기반 실질적 질문 및 키워드)
GOLDEN_DATASET = [
    {
        "query": "how to perform AND queries in django orm",
        "expected_keywords": ["AND", "filter", "Q objects"],
        "category": "Querying",
    },
    {
        "query": "how to group records using annotate or aggregate",
        "expected_keywords": ["annotate", "Count", "Sum", "group by"],
        "category": "Aggregation",
    },
    {
        "query": "order query results by descending or ascending",
        "expected_keywords": ["order_by", "desc()", "asc()"],
        "category": "Ordering",
    },
    {
        "query": "defining foreign key and one to one relationships",
        "expected_keywords": ["ForeignKey", "OneToOneField", "related_name"],
        "category": "Modelling",
    },
    {
        "query": "how to write unit tests for django models",
        "expected_keywords": ["TestCase", "setUp", "assert"],
        "category": "Testing",
    },
]


async def evaluate() -> None:
    """하이브리드 검색 및 Rerank 품질을 골든 데이터셋으로 평가합니다."""
    search_service = get_search_service()

    total_queries = len(GOLDEN_DATASET)
    hit_at_3 = 0
    mrr_sum: float = 0.0

    print(f"--- Search Quality Evaluation (Total Queries: {total_queries}) ---\n")

    for entry in GOLDEN_DATASET:
        query: str = str(entry["query"])
        expected: list[str] = entry["expected_keywords"]  # type: ignore

        # 통합 검색 실행
        results = await search_service.search(query, limit=5)

        found_rank = 0
        is_hit_3 = False

        for i, res in enumerate(results):
            rank = i + 1
            content = res["content"]

            # 정답 판별 (키워드 매칭 방식)
            is_correct = any(kw.lower() in content.lower() for kw in expected)

            if is_correct and found_rank == 0:
                found_rank = rank
                if rank <= 3:
                    is_hit_3 = True

        if found_rank > 0:
            mrr_sum += 1.0 / found_rank
        if is_hit_3:
            hit_at_3 += 1

        print(f"Query: {query}")
        print(
            f"Rank: {found_rank if found_rank > 0 else 'N/A'}, Hit@3: {'Yes' if is_hit_3 else 'No'}"
        )
        print("-" * 20)

    # 지표 계산
    final_mrr = mrr_sum / total_queries
    final_hit_rate_3 = (hit_at_3 / total_queries) * 100

    print("\n[Final Metrics]")
    print(f"- MRR: {final_mrr:.4f}")
    print(f"- Hit Rate@3: {final_hit_rate_3:.2f}%")

    if final_mrr >= 0.15:
        print("✓ MRR target goal might be achieved.")


if __name__ == "__main__":
    asyncio.run(evaluate())
