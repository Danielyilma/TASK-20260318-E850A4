import enum


class UserRole(str, enum.Enum):
    applicant = "applicant"
    reviewer = "reviewer"
    financial_admin = "financial_admin"
    system_admin = "system_admin"


class RegistrationStatus(str, enum.Enum):
    draft = "draft"
    submitted = "submitted"
    needs_correction = "needs_correction"
    supplemented = "supplemented"
    approved = "approved"
    rejected = "rejected"
    canceled = "canceled"
    waitlisted = "waitlisted"


class MaterialVersionLabel(str, enum.Enum):
    pending_submission = "pending_submission"
    submitted = "submitted"
    needs_correction = "needs_correction"


class TransactionType(str, enum.Enum):
    income = "income"
    expense = "expense"


class ReviewAction(str, enum.Enum):
    approve = "approve"
    reject = "reject"
    request_correction = "request_correction"
    waitlist = "waitlist"
    cancel = "cancel"


class BatchCollectionStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"


class AlertSeverity(str, enum.Enum):
    info = "info"
    warning = "warning"
    critical = "critical"
