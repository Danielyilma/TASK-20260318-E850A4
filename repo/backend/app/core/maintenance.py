"""Process-wide maintenance lock used during one-click restore."""

from __future__ import annotations

import threading

_lock = threading.Lock()
_active = False


def is_maintenance_mode() -> bool:
    return _active


def enter_maintenance() -> None:
    global _active
    with _lock:
        _active = True


def leave_maintenance() -> None:
    global _active
    with _lock:
        _active = False
