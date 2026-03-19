from collections.abc import Generator
from typing import Any

import pytest
from django.db import connections


def _close_all_connections() -> None:
    """모든 활성 데이터베이스 커넥션을 닫습니다."""
    for conn in connections.all():
        conn.close()


@pytest.fixture(autouse=True)
def db_connection_cleanup() -> Generator[None]:
    """
    각 테스트가 완료될 때마다 데이터베이스 커넥션을 정리합니다.
    비동기 작업으로 인해 남을 수 있는 커넥션 유출을 방지합니다.
    """
    yield
    _close_all_connections()


@pytest.fixture(scope="session", autouse=True)
def session_db_cleanup(request: Any) -> None:
    """테스트 세션 전체 종료 시 최종 정리."""

    def finalizer() -> None:
        _close_all_connections()

    request.addfinalizer(finalizer)
