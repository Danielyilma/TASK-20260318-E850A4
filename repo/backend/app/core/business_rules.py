from decimal import Decimal

# Overspend Threshold (110% of approved budget)
OVERSPEND_THRESHOLD_MULTIPLIER = Decimal("1.10")

# Quality Alert Thresholds
APPROVAL_RATE_MIN_THRESHOLD = 50.0  # percentage
CORRECTION_RATE_MAX_THRESHOLD = 30.0  # percentage
OVERSPENDING_RATE_MAX_THRESHOLD = 15.0  # percentage
