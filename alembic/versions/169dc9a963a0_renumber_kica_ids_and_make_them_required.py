"""renumber kica ids and make them required

Revision ID: 169dc9a963a0
Revises: 2d2494580706
Create Date: 2026-11-04 16:04:21.101676

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '169dc9a963a0'
down_revision: Union[str, Sequence[str], None] = '2d2494580706'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# The "S" players move into the gap after KICA049, in the same order
RENUMBER = [
    ("KICA_101S", "KICA050"),
    ("KICA_102S", "KICA051"),
    ("KICA_103S", "KICA052"),
    ("KICA_104S", "KICA053"),
    ("KICA_105S", "KICA054"),
    ("KICA_106S", "KICA055"),
    ("KICA_107S", "KICA056"),
    ("KICA_108S", "KICA057"),
]


def upgrade() -> None:
    # 1. KICA_001 ... KICA_049  ->  KICA001 ... KICA049
    op.execute("""
        UPDATE players
        SET kica_id = replace(kica_id, '_', '')
        WHERE kica_id ~ '^KICA_[0-9]{3}$'
    """)

    # 2. The S players  ->  KICA050 ... KICA057
    for old_id, new_id in RENUMBER:
        op.execute(
            sa.text("UPDATE players SET kica_id = :new_id WHERE kica_id = :old_id")
            .bindparams(old_id=old_id, new_id=new_id)
        )

    # 3. Safety check: stop if any player still has an old-style or missing ID
    leftover = op.get_bind().execute(sa.text("""
        SELECT name, kica_id FROM players
        WHERE kica_id IS NULL OR kica_id !~ '^KICA[0-9]{3,}$'
    """)).all()

    if leftover:
        raise RuntimeError(f"These players still need a proper KICA ID: {leftover}")

    # 4. Every player now has an ID, so make it required
    op.alter_column('players', 'kica_id', existing_type=sa.String(length=20), nullable=False)


def downgrade() -> None:
    op.alter_column('players', 'kica_id', existing_type=sa.String(length=20), nullable=True)

    for old_id, new_id in RENUMBER:
        op.execute(
            sa.text("UPDATE players SET kica_id = :old_id WHERE kica_id = :new_id")
            .bindparams(old_id=old_id, new_id=new_id)
        )

    op.execute("""
        UPDATE players
        SET kica_id = 'KICA_' || substring(kica_id from 5)
        WHERE kica_id ~ '^KICA[0-9]{3}$'
    """)