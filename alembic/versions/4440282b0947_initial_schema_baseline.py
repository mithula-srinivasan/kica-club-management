"""initial schema baseline

Revision ID: 4440282b0947
Revises: 
Create Date: 2026-10-11 12:32:39.156105

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4440282b0947'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # These four tables were first created by create_tables.py, before Alembic was set up.
    # Creating them here means a brand-new database can be built with "alembic upgrade head" alone.
    op.create_table('execs',
    sa.Column('exec_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('role', sa.String(length=20), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('exec_id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('players',
    sa.Column('player_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('joined_on', sa.Date(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('player_id')
    )
    op.create_table('club_sessions',
    sa.Column('session_id', sa.Integer(), nullable=False),
    sa.Column('session_date', sa.Date(), nullable=False),
    sa.Column('is_finalized', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('session_id'),
    sa.UniqueConstraint('session_date')
    )
    op.create_table('attendance',
    sa.Column('attendance_id', sa.Integer(), nullable=False),
    sa.Column('session_id', sa.Integer(), nullable=False),
    sa.Column('player_id', sa.Integer(), nullable=False),
    sa.Column('is_present', sa.Boolean(), nullable=False),
    sa.Column('marked_by_exec_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['marked_by_exec_id'], ['execs.exec_id'], ),
    sa.ForeignKeyConstraint(['player_id'], ['players.player_id'], ),
    sa.ForeignKeyConstraint(['session_id'], ['club_sessions.session_id'], ),
    sa.PrimaryKeyConstraint('attendance_id'),
    sa.UniqueConstraint('session_id', 'player_id', name='uq_session_player')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('attendance')
    op.drop_table('club_sessions')
    op.drop_table('players')
    op.drop_table('execs')
