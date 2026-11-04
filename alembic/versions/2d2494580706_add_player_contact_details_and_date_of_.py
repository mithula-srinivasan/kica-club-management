"""add player contact details and date of birth

Revision ID: 2d2494580706
Revises: 88ef4129e1f5
Create Date: 2026-11-04 15:07:07.999624

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2d2494580706'
down_revision: Union[str, Sequence[str], None] = '88ef4129e1f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add the columns, allowing empty for now (current players have no values yet)
    op.add_column('players', sa.Column('phone_1', sa.String(length=30), nullable=True))
    op.add_column('players', sa.Column('phone_2', sa.String(length=30), nullable=True))
    op.add_column('players', sa.Column('email', sa.String(length=255), nullable=True))
    op.add_column('players', sa.Column('parent_name', sa.String(length=100), nullable=True))
    op.add_column('players', sa.Column('fide_id', sa.String(length=20), nullable=True))
    op.add_column('players', sa.Column('gender', sa.String(length=10), nullable=True))
    op.add_column('players', sa.Column('date_of_birth', sa.Date(), nullable=True))

    # 2. Give every current player demo values, which Execs will replace later
    op.execute("""
        UPDATE players
        SET phone_1 = '+965 0000 0000',
            email = 'update.me@example.com',
            parent_name = 'To be updated',
            date_of_birth = DATE '2000-01-01'
    """)

    # 3. Now that no player is empty, make the required columns NOT NULL
    op.alter_column('players', 'phone_1', nullable=False)
    op.alter_column('players', 'email', nullable=False)
    op.alter_column('players', 'parent_name', nullable=False)
    op.alter_column('players', 'date_of_birth', nullable=False)

    # 4. Only allow these genders (or empty)
    op.create_check_constraint(
        'ck_player_gender',
        'players',
        "gender IN ('male', 'female', 'other')"
    )


def downgrade() -> None:
    op.drop_constraint('ck_player_gender', 'players', type_='check')
    op.drop_column('players', 'date_of_birth')
    op.drop_column('players', 'gender')
    op.drop_column('players', 'fide_id')
    op.drop_column('players', 'parent_name')
    op.drop_column('players', 'email')
    op.drop_column('players', 'phone_2')
    op.drop_column('players', 'phone_1')
