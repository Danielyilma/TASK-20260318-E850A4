import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint_returns_ok(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_health_endpoint_returns_503_when_database_errors(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from sqlalchemy.exc import SQLAlchemyError

    from app.services import health_service as hs

    def _raise(self, db):
        raise SQLAlchemyError("database unavailable")

    monkeypatch.setattr(hs.HealthService, "check_database", _raise)

    response = await client.get("/api/v1/health")
    assert response.status_code == 503
    body = response.json()
    assert body["error"]["code"] == "INTERNAL_ERROR"
    assert "Database" in body["error"]["message"]
