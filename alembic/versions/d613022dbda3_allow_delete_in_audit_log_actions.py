"""allow DELETE in audit log actions

Revision ID: d613022dbda3
Revises: 64d04d02f967
Create Date: 2026-10-29 22:39:19.660866

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd613022dbda3'
down_revision: Union[str, Sequence[str], None] = '64d04d02f967'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint('ck_audit_action', 'audit_logs', type_='check')
    op.create_check_constraint(
        'ck_audit_action',
        'audit_logs',
        "action IN ('CREATE', 'UPDATE', 'DELETE', 'REVERSE', 'FINALIZE')"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('ck_audit_action', 'audit_logs', type_='check')
    op.create_check_constraint(
        'ck_audit_action',
        'audit_logs',
        "action IN ('CREATE', 'UPDATE', 'REVERSE', 'FINALIZE')"
    )
