import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

# 표준 로깅 설정
logger = logging.getLogger("mcp_search")
logger.setLevel(logging.INFO)


# stdout으로 출력하는 핸들러 (JSON 형식)
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)
        return json.dumps(log_data, ensure_ascii=False)


handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(JsonFormatter())
logger.addHandler(handler)


def log_tool_call(
    tool_name: str, query: str, results: list[dict[str, Any]], params: dict[str, Any]
):
    """도구 호출 정보를 구조화된 JSON으로 로깅합니다."""
    top_results = []
    chunk_ids = []

    for res in results[:3]:
        top_results.append(
            {
                "title": res.get("document_title") or res.get("title") or "No Title",
                "score": res.get("relevance_score") or res.get("similarity") or 0.0,
            }
        )

    for res in results:
        if "id" in res:
            chunk_ids.append(res["id"])

    extra_data = {
        "event": "tool_call",
        "tool": tool_name,
        "query": query,
        "params": params,
        "results_count": len(results),
        "top_results": top_results,
        "chunk_ids": chunk_ids,
    }

    # 헌법 V.3 준수: 구조화된 로그 출력
    logger.info(f"Tool {tool_name} called with query: {query}", extra={"extra_data": extra_data})
