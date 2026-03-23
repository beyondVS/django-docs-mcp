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

# US3: 골든 데이터셋 정의 (Django 5.2 공식 문서 및 Cookbook 기반 현실적 질의 30선)
# LLM 에이전트나 숙련된 개발자가 던질 법한 구체적인 질의 패턴을 반영합니다.
GOLDEN_DATASET = [
    # 1. Models & Migrations
    {
        "query": "How to use GeneratedField in Django 5.2 models for database-level computed columns?",
        "expected_keywords": ["GeneratedField", "db_persist", "models.GeneratedField"],
        "category": "Models",
    },
    {
        "query": "I need to create a unique constraint on multiple fields using the newer UniqueConstraint class.",
        "expected_keywords": ["UniqueConstraint", "constraints", "models.UniqueConstraint"],
        "category": "Models",
    },
    # 2. ORM & Querying (Cookbook + Official Docs)
    {
        "query": "Show me the best way to optimize a QuerySet that joins multiple related tables to avoid N+1 issues.",
        "expected_keywords": ["select_related", "prefetch_related", "N+1"],
        "category": "ORM",
    },
    {
        "query": "How can I perform a complex OR condition in a filter using Q objects?",
        "expected_keywords": ["Q objects", "| operator", "complex lookups"],
        "category": "ORM",
    },
    {
        "query": "Example of using F expressions to update a counter field atomically without race conditions.",
        "expected_keywords": ["F()", "F expressions", "atomic update"],
        "category": "ORM",
    },
    {
        "query": "How to execute a subquery that checks for existence in another table?",
        "expected_keywords": ["Exists", "Subquery", "OuterRef"],
        "category": "ORM",
    },
    # 3. Forms & Validation
    {
        "query": "How to implement a custom clean method in a Django Form to validate inter-field dependencies?",
        "expected_keywords": ["def clean(self)", "ValidationError", "cleaned_data"],
        "category": "Forms",
    },
    {
        "query": "Show me how to render a Django form manually in a template instead of using as_p().",
        "expected_keywords": ["form.field", "form.errors", "label_tag"],
        "category": "Forms",
    },
    # 4. Views & URLconfs
    {
        "query": "I want to create a Class-Based View (CBV) for updating a model instance with proper mixins.",
        "expected_keywords": ["UpdateView", "LoginRequiredMixin", "success_url"],
        "category": "Views",
    },
    {
        "query": "How to use path converters in URLconf to capture a UUID or custom slug pattern?",
        "expected_keywords": ["path('<uuid:", "register_converter", "slug"],
        "category": "Views",
    },
    # 5. Templates & UI
    {
        "query": "What is the correct syntax for template inheritance and block overriding in Django?",
        "expected_keywords": ["{% extends", "{% block", "base.html"],
        "category": "Templates",
    },
    {
        "query": "How to create a custom template tag that takes arguments and returns a value?",
        "expected_keywords": ["register.simple_tag", "template.Library", "load"],
        "category": "Templates",
    },
    # 6. Admin Interface
    {
        "query": "How to customize the list_display and search_fields in the Django Admin for a specific model?",
        "expected_keywords": ["list_display", "search_fields", "admin.ModelAdmin"],
        "category": "Admin",
    },
    {
        "query": "I want to add a custom action to the Django Admin to perform bulk updates on selected items.",
        "expected_keywords": ["admin.action", "actions =", "make_published"],
        "category": "Admin",
    },
    # 7. Security & Authentication
    {
        "query": "What are the recommended security settings for a production Django deployment (CSRF, SSL, etc.)?",
        "expected_keywords": ["SECURE_SSL_REDIRECT", "CSRF_COOKIE_SECURE", "deployment"],
        "category": "Security",
    },
    {
        "query": "How to implement a custom user model that inherits from AbstractUser.",
        "expected_keywords": ["AbstractUser", "AUTH_USER_MODEL", "BaseUserManager"],
        "category": "Auth",
    },
    # 8. Async & Performance
    {
        "query": "How to write an asynchronous view in Django using async def and sync_to_async?",
        "expected_keywords": ["async def", "sync_to_async", "database_sync_to_async"],
        "category": "Async",
    },
    {
        "query": "Show me how to use the async ORM methods like aget() or afirst() in Django 5.x.",
        "expected_keywords": ["aget(", "afirst(", "await"],
        "category": "Async",
    },
    # 9. Middleware & Signals
    {
        "query": "How to write a custom middleware to log every request and response in Django?",
        "expected_keywords": ["get_response", "__call__", "MiddlewareMixin"],
        "category": "Middleware",
    },
    {
        "query": "Example of using signals like post_save to trigger actions after a model is created.",
        "expected_keywords": ["@receiver", "post_save", "sender"],
        "category": "Signals",
    },
    # 10. Generic Documentation & Troubleshooting
    {
        "query": "Where can I find information on setting up Django with PostgreSQL using the psycopg driver?",
        "expected_keywords": ["psycopg2", "ENGINE", "django.db.backends.postgresql"],
        "category": "Setup",
    },
    {
        "query": "How to configure logging in Django to write errors to a specific file?",
        "expected_keywords": ["LOGGING", "handlers", "RotatingFileHandler"],
        "category": "Config",
    },
]


async def evaluate() -> None:
    """하이브리드 검색 및 Late Interaction 리랭킹 품질을 골든 데이터셋으로 평가합니다."""
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

        print(f"[{entry['category']}] Query: {query}")
        print(
            f"Rank: {found_rank if found_rank > 0 else 'N/A'}, Hit@3: {'Yes' if is_hit_3 else 'No'}"
        )
        print("-" * 20)

    # 지표 계산
    final_mrr = mrr_sum / total_queries
    final_hit_rate_3 = (hit_at_3 / total_queries) * 100

    print("\n[Final Metrics]")
    print(f"- MRR: {final_mrr:.4f} (Target: > 0.75)")
    print(f"- Hit Rate@3: {final_hit_rate_3:.2f}% (Target: > 90%)")

    # 헌법(v2.0.0) 기준 평가
    if final_mrr >= 0.75 and final_hit_rate_3 >= 90:
        print("\n✅ Search quality meets the project constitution standards.")
    else:
        print("\n⚠️ Search quality is below the target goals. Further tuning required.")


if __name__ == "__main__":
    asyncio.run(evaluate())
