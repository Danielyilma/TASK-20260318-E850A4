from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.http_errors import forbidden
from app.core.time import utcnow
from app.models.enums import UserRole
from app.models.registration import Registration
from app.models.sensitive_verification_audit import SensitiveVerificationAudit
from app.models.user import User
from app.schemas.registration_domain import SensitiveVerifyResponse
from app.services.audit_log_service import AuditLogService
from app.services.phase4_access import ensure_registration, ensure_registration_access


class Phase4SensitiveService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def verify_sensitive(self, reviewer: User, registration_id: uuid.UUID, *, ip_address: str = "unknown") -> SensitiveVerifyResponse:
        if reviewer.role != UserRole.reviewer:
            raise forbidden("FORBIDDEN", "Only reviewers can verify sensitive data")
        reg = ensure_registration(self.db.get(Registration, registration_id))
        ensure_registration_access(reviewer, reg)
        applicant = self.db.get(User, reg.applicant_id)
        if applicant is None:
            raise forbidden("FORBIDDEN", "Applicant not found")

        now = utcnow()
        audit = SensitiveVerificationAudit(
            id=uuid.uuid4(),
            registration_id=reg.id,
            reviewer_id=reviewer.id,
            created_at=now,
        )
        self.db.add(audit)
        AuditLogService(self.db).append(
            user_id=reviewer.id,
            username=reviewer.username,
            action="verify_sensitive",
            resource_type="registration",
            resource_id=reg.id,
            details={"sensitive_verification_audit_id": str(audit.id)},
            ip_address=ip_address,
        )
        self.db.commit()
        self.db.refresh(audit)
        return SensitiveVerifyResponse(
            registration_id=reg.id,
            applicant_id=applicant.id,
            id_number=applicant.id_number,
            contact_info=applicant.contact_info,
            verified_at=audit.created_at,
            audit_log_id=audit.id,
        )
