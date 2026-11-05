"""add country to players and registrations

Revision ID: 405834e35ae3
Revises: bebf10a1667f
Create Date: 2026-11-05 20:14:14.670501

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '405834e35ae3'
down_revision: Union[str, Sequence[str], None] = 'bebf10a1667f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add the columns, allowing empty for now
    op.add_column('players', sa.Column('country', sa.String(length=100), nullable=True))
    op.add_column('player_registrations', sa.Column('country', sa.String(length=100), nullable=True))

    # 2. Existing rows get a demo value, which Execs will replace later
    op.execute("UPDATE players SET country = 'To be updated'")
    op.execute("UPDATE player_registrations SET country = 'To be updated'")

    # 3. Now nobody is empty, so make it required
    op.alter_column('players', 'country', existing_type=sa.String(length=100), nullable=False)
    op.alter_column('player_registrations', 'country', existing_type=sa.String(length=100), nullable=False)


def downgrade() -> None:
    op.drop_column('player_registrations', 'country')
    op.drop_column('players', 'country')