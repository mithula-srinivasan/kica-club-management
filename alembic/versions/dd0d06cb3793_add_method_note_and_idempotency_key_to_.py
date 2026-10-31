"""add method, note and idempotency key to payments

Revision ID: dd0d06cb3793
Revises: d3c931f8f490
Create Date: 2026-10-31 12:21:23.601571

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dd0d06cb3793'
down_revision: Union[str, Sequence[str], None] = 'd3c931f8f490'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('payments', sa.Column('method', sa.String(length=20), server_default='cash', nullable=False))
    op.add_column('payments', sa.Column('note', sa.Text(), nullable=True))
    op.add_column('payments', sa.Column('idempotency_key', sa.String(length=64), nullable=True))
    op.create_check_constraint('ck_payment_method', 'payments', "method IN ('cash', 'bank_transfer')")
    op.create_unique_constraint('uq_payments_idempotency_key', 'payments', ['idempotency_key'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_payments_idempotency_key', 'payments', type_='unique')
    op.drop_constraint('ck_payment_method', 'payments', type_='check')
    op.drop_column('payments', 'idempotency_key')
    op.drop_column('payments', 'note')
    op.drop_column('payments', 'method')
