"""add starting fee rate

Revision ID: d3c931f8f490
Revises: d613022dbda3
Create Date: 2026-10-31 10:52:11.485614

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3c931f8f490'
down_revision: Union[str, Sequence[str], None] = 'd613022dbda3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # The club has always charged 5 KWD a month, so the rate applies from long before the app
    op.execute(
        "INSERT INTO fee_rates (monthly_amount, effective_from) "
        "VALUES (5.000, '2000-01-01')"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DELETE FROM fee_rates WHERE effective_from = '2000-01-01'")
