"""initial schema placeholder

Revision ID: 20260421_000001
Revises:
Create Date: 2026-04-21

"""

from typing import Sequence, Union

revision: str = "20260421_000001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
