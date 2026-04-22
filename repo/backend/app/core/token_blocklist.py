_revoked_jtis: set[str] = set()


def clear_blocklist() -> None:
    _revoked_jtis.clear()


def revoke_jti(jti: str) -> None:
    _revoked_jtis.add(jti)


def is_jti_revoked(jti: str) -> bool:
    return jti in _revoked_jtis
