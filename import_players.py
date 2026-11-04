from datetime import date
from pathlib import Path

from openpyxl import load_workbook
from sqlalchemy import select

from database import SessionLocal
from models import Player


EXCEL_FILE = Path("Members Fee Collection New copy.xlsx")


def clean_text(value):
    """Remove extra spaces from names."""
    return " ".join(str(value).split())


def import_players():
    workbook = load_workbook(EXCEL_FILE, data_only=True)
    sheet = workbook.active

    players_to_import = []
    seen_ids = set()

    # Row 2 contains the column headings.
    for row_number, row in enumerate(
        sheet.iter_rows(min_row=3, values_only=True),
        start=3
    ):
        player_name = row[1]   # Column B
        parent_name = row[2]   # Column C
        kica_id = row[3]       # Column D

        # Ignore rows without a KICA ID.
        if kica_id is None or not str(kica_id).strip():
            continue

        if not player_name or not parent_name:
            raise ValueError(
                f"Missing player or parent name on row {row_number}"
            )

        kica_id = clean_text(kica_id)
        full_name = (
            f"{clean_text(player_name)} "
            f"{clean_text(parent_name)}"
        )

        if kica_id in seen_ids:
            raise ValueError(f"Duplicate KICA ID: {kica_id}")

        seen_ids.add(kica_id)

        players_to_import.append({
            "kica_id": kica_id,
            "name": full_name
        })

    # Check that we're reading the expected member list.
    if len(players_to_import) != 57:
        raise ValueError(
            f"Expected 57 players, found {len(players_to_import)}"
        )

    with SessionLocal() as db:
        existing_players = {
            player.kica_id: player
            for player in db.scalars(select(Player)).all()
            if player.kica_id is not None
        }

        added = 0
        skipped = 0

        for data in players_to_import:
            kica_id = data["kica_id"]
            name = data["name"]

            if kica_id in existing_players:
                if existing_players[kica_id].name != name:
                    raise ValueError(
                        f"Name mismatch for {kica_id}: "
                        f"database has '{existing_players[kica_id].name}', "
                        f"Excel has '{name}'"
                    )

                skipped += 1
                continue

            new_player = Player(
                kica_id=kica_id,
                name=name,
                joined_on=None,
                is_active=True,
                phone_1="+965 0000 0000",
                email="update.me@example.com",
                parent_name="To be updated",
                date_of_birth=date(2000, 1, 1),
            )

            db.add(new_player)
            added += 1

        # All new records are saved together.
        db.commit()

    print(f"Successfully imported {added} players!")
    print(f"Skipped {skipped} existing players.")


if __name__ == "__main__":
    import_players()
