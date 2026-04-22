from sqlalchemy.orm import Session

from app.services.health_service import HealthService


def test_health_service_checks_database(db_session: Session) -> None:
    assert HealthService().check_database(db_session) is True
