from datetime import date, datetime
from decimal import Decimal
from io import BytesIO

from fastapi import APIRouter, Depends, Response
from openpyxl import Workbook
from openpyxl.styles import Font
from sqlalchemy import select
from sqlalchemy.orm import Session

from balances import (
    all_player_balances,
    apply_oldest_first,
    cash_held_by_exec,
    fees_by_player,
    include_opening_balance,
    opening_balances_by_player,
    paid_by_player,
)
from club_time import KUWAIT, kuwait_today
from dependencies import get_db, require_admin
from fees import ZERO
from models import (
    Attendance,
    ClubSession,
    Exec,
    ExecOpeningBalance,
    Income,
    Expense,
    Payment,
    Player,
    PlayerOpeningBalance,
    Transfer,
)


router = APIRouter(
    prefix="/exports",
    tags=["Exports"],
    dependencies=[Depends(require_admin)]
)

EXCEL_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def excel_value(value):
    # Excel cannot store time zones, so times are converted to Kuwait time first
    if isinstance(value, datetime):
        return value.astimezone(KUWAIT).replace(tzinfo=None)
    return value


def add_sheet(workbook, title, headers, rows, date_format="dd mmm yyyy"):
    sheet = workbook.create_sheet(title)
    sheet.append(headers)

    for cell in sheet[1]:
        cell.font = Font(bold=True)

    for row in rows:
        sheet.append([excel_value(value) for value in row])

        for cell in sheet[sheet.max_row]:
            if isinstance(cell.value, Decimal):
                cell.number_format = "0.000"
            elif isinstance(cell.value, datetime):
                cell.number_format = "dd mmm yyyy hh:mm"
            elif isinstance(cell.value, date):
                cell.number_format = date_format

    # Keep the header row visible while scrolling, and make columns wide enough to read
    sheet.freeze_panes = "A2"

    for column in sheet.columns:
        longest = max(len(str(cell.value)) for cell in column if cell.value is not None)
        sheet.column_dimensions[column[0].column_letter].width = min(longest + 3, 50)

    return sheet


@router.get("/club-data")
def export_club_data(db: Session = Depends(get_db)):
    exec_names = dict(db.execute(select(Exec.exec_id, Exec.name)).all())
    players = db.scalars(select(Player).order_by(Player.name)).all()
    balances = {row["player_id"]: row for row in all_player_balances(db)}
    cash_held = cash_held_by_exec(db)

    workbook = Workbook()
    workbook.remove(workbook.active)

    # Summary
    summary_rows = [
        ["Created", datetime.now(KUWAIT)],
        ["Club balance (KWD)", sum((row["amount"] for row in cash_held), ZERO)],
        ["Owed by members (KWD)", sum((row["outstanding"] for row in balances.values()), ZERO)],
        ["Paid in advance (KWD)", sum((row["credit"] for row in balances.values()), ZERO)],
        ["Active players", sum(1 for player in players if player.is_active)],
        [],
        ["Cash held by", "Amount (KWD)"],
    ]
    summary_rows += [[row["name"], row["amount"]] for row in cash_held]
    add_sheet(workbook, "Summary", ["KICA club data", ""], summary_rows)

    # Players
    add_sheet(
        workbook,
        "Players",
        ["KICA ID", "Name", "Joined", "Status", "Owes (KWD)", "Paid in advance (KWD)"],
        [
            [
                player.kica_id,
                player.name,
                player.joined_on,
                "Active" if player.is_active else "Inactive",
                balances.get(player.player_id, {}).get("outstanding", ZERO),
                balances.get(player.player_id, {}).get("credit", ZERO),
            ]
            for player in players
        ],
    )

    # Monthly fees, worked out the same way as each player's statement
    grouped = fees_by_player(db)
    paid_totals = paid_by_player(db)
    openings = opening_balances_by_player(db)
    fee_rows = []

    for player in players:
        if player.player_id not in grouped and player.player_id not in openings:
            continue

        fees, paid = include_opening_balance(
            grouped.get(player.player_id, []),
            paid_totals.get(player.player_id, ZERO),
            openings.get(player.player_id),
        )
        months, _ = apply_oldest_first(fees, paid)

        for month in months:
            fee_rows.append([
                player.name,
                player.kica_id,
                "Owed from before" if month["is_opening_balance"] else month["fee_month"],
                month["amount_due"],
                month["amount_paid"],
                month["remaining"],
            ])

    add_sheet(
        workbook,
        "Monthly fees",
        ["Player", "KICA ID", "Month", "Fee (KWD)", "Paid (KWD)", "Still to pay (KWD)"],
        fee_rows,
        date_format="mmm yyyy",
    )

    # Payments
    player_names = {player.player_id: player.name for player in players}
    payments = db.scalars(select(Payment).order_by(Payment.paid_on, Payment.payment_id)).all()

    add_sheet(
        workbook,
        "Payments",
        ["Payment ID", "Date paid", "Player", "Amount (KWD)", "Method", "Note",
         "Collected by", "Status", "Recorded at"],
        [
            [
                p.payment_id,
                p.paid_on,
                player_names[p.player_id],
                p.amount,
                "Bank transfer" if p.method == "bank_transfer" else "Cash",
                p.note,
                exec_names[p.collected_by_exec_id],
                p.status,
                p.created_at,
            ]
            for p in payments
        ],
    )

    # Expenses
    expenses = db.scalars(select(Expense).order_by(Expense.expense_date, Expense.expense_id)).all()

    add_sheet(
        workbook,
        "Expenses",
        ["Expense ID", "Date", "Description", "Amount (KWD)", "Paid by", "Status", "Recorded at"],
        [
            [
                e.expense_id,
                e.expense_date,
                e.description,
                e.amount,
                exec_names[e.paid_by_exec_id],
                e.status,
                e.created_at,
            ]
            for e in expenses
        ],
    )

        # Income
    entries = db.scalars(select(Income).order_by(Income.income_date, Income.income_id)).all()

    add_sheet(
        workbook,
        "Income",
        ["Income ID", "Date", "Description", "Amount (KWD)", "Received by", "Status", "Recorded at"],
        [
            [
                i.income_id,
                i.income_date,
                i.description,
                i.amount,
                exec_names[i.received_by_exec_id],
                i.status,
                i.created_at,
            ]
            for i in entries
        ],
    )

    # Transfers
    transfers = db.scalars(select(Transfer).order_by(Transfer.transferred_at, Transfer.transfer_id)).all()

    add_sheet(
        workbook,
        "Transfers",
        ["Transfer ID", "Date", "From", "To", "Amount (KWD)", "Recorded by", "Status"],
        [
            [
                t.transfer_id,
                t.transferred_at.astimezone(KUWAIT).date(),
                exec_names[t.from_exec_id],
                exec_names[t.to_exec_id],
                t.amount,
                exec_names[t.recorded_by_exec_id],
                t.status,
            ]
            for t in transfers
        ],
    )

    # Attendance: one row per player present at each session
    attendance_rows = db.execute(
        select(ClubSession.session_date, Player.name, Player.kica_id)
        .join(Attendance, Attendance.session_id == ClubSession.session_id)
        .join(Player, Player.player_id == Attendance.player_id)
        .where(Attendance.is_present.is_(True))
        .order_by(ClubSession.session_date, Player.name)
    ).all()

    add_sheet(
        workbook,
        "Attendance",
        ["Session date", "Player", "KICA ID"],
        [list(row) for row in attendance_rows],
    )

    # Opening balances
    opening_rows = [
        ["Exec cash", exec_names[row.exec_id], row.amount, row.as_of]
        for row in db.scalars(select(ExecOpeningBalance))
    ]
    opening_rows += [
        ["Member balance", player_names[row.player_id], row.amount, row.as_of]
        for row in db.scalars(select(PlayerOpeningBalance))
    ]

    add_sheet(
        workbook,
        "Opening balances",
        ["Type", "Name", "Amount (KWD, negative = paid in advance)", "As of"],
        opening_rows,
    )

    buffer = BytesIO()
    workbook.save(buffer)
    filename = f"KICA-data-{kuwait_today().isoformat()}.xlsx"

    return Response(
        content=buffer.getvalue(),
        media_type=EXCEL_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )