"""revoked_tokens

Revision ID: 20260428_000008
Revises: 20260427_000007
Create Date: 2026-04-28 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260428_000008'
down_revision = '20260427_000007'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'revoked_tokens',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('jti', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_by', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['revoked_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_revoked_tokens_expires_at'), 'revoked_tokens', ['expires_at'], unique=False)
    op.create_index(op.f('ix_revoked_tokens_jti'), 'revoked_tokens', ['jti'], unique=True)

def downgrade() -> None:
    op.drop_index(op.f('ix_revoked_tokens_jti'), table_name='revoked_tokens')
    op.drop_index(op.f('ix_revoked_tokens_expires_at'), table_name='revoked_tokens')
    op.drop_table('revoked_tokens')
