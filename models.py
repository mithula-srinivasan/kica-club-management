from datetime import date, datetime, timezone

from sqlalchemy import (
    String,
    Boolean,
    Date,
    ForeignKey,
    UniqueConstraint,
    Numeric,
    CheckConstraint,
    Text,
    DateTime,
    func,
    JSON
)

from decimal import Decimal
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Exec(Base):
    __tablename__ = "execs"

    exec_id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )

    password_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    role: Mapped[str] = mapped_column(
        String(20),
        default="exec",
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

        # NULL means the sign-up is still waiting for an admin to approve it
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    approved_by_exec_id: Mapped[int | None] = mapped_column(
        ForeignKey("execs.exec_id"),
        nullable=True
    )


class ExecSession(Base):
    __tablename__ = "exec_sessions"

    session_id: Mapped[int] = mapped_column(primary_key=True)

    exec_id: Mapped[int] = mapped_column(
        ForeignKey("execs.exec_id"),
        index=True,
        nullable=False
    )

    # SHA-256 hash of the session token; the raw token only lives in the cookie
    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )


class PasswordSetupToken(Base):
    __tablename__ = "password_setup_tokens"

    token_id: Mapped[int] = mapped_column(primary_key=True)

    exec_id: Mapped[int] = mapped_column(
        ForeignKey("execs.exec_id"),
        index=True,
        nullable=False
    )

    # SHA-256 hash of the setup token; the raw token only appears in the link
    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False
    )

    created_by_exec_id: Mapped[int] = mapped_column(
        ForeignKey("execs.exec_id"),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    # Set when the link is used, so it can never be used again
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )


class Player(Base):
    __tablename__ = "players"

    player_id: Mapped[int] = mapped_column(primary_key=True)

    kica_id: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    joined_on: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    # Required for every player (current players were given demo values in the migration)
    phone_1: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)

    # Optional
    phone_2: Mapped[str | None] = mapped_column(String(30), nullable=True)
    fide_id: Mapped[str | None] = mapped_column(String(20), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(10), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "gender IN ('male', 'female', 'other')",
            name="ck_player_gender"
        ),
    )


class ClubSession(Base):
    __tablename__ = "club_sessions"

    session_id: Mapped[int] = mapped_column(primary_key=True)

    session_date: Mapped[date] = mapped_column(
        Date,
        unique=True,
        nullable=False
    )

    is_finalized: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )


class Attendance(Base):
    __tablename__ = "attendance"

    attendance_id: Mapped[int] = mapped_column(
        primary_key=True
    )

    session_id: Mapped[int] = mapped_column(
        ForeignKey("club_sessions.session_id"),
        nullable=False
    )

    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.player_id"),
        nullable=False
    )

    is_present: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    marked_by_exec_id: Mapped[int] = mapped_column(
        ForeignKey("execs.exec_id"),
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "session_id",
            "player_id",
            name="uq_session_player"
        ),
    )

class FeeRate(Base):
    __tablename__ = "fee_rates"

    fee_rate_id: Mapped[int] = mapped_column(
        primary_key=True
    )

    monthly_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 3),
        nullable=False
    )

    effective_from: Mapped[date] = mapped_column(
        Date,
        unique=True,
        nullable=False
    )

    changed_by_exec_id: Mapped[int | None] = mapped_column(
        ForeignKey("execs.exec_id"),
        nullable=True
    )

    __table_args__ = (
        CheckConstraint(
            "monthly_amount > 0",
            name="ck_fee_rate_positive"
        ),
    )

class FeeAdjustment(Base):
    __tablename__ = "fee_adjustments"

    adjustment_id: Mapped[int] = mapped_column(
        primary_key=True
    )

    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.player_id"),
        nullable=False
    )

    fee_month: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    amount_change: Mapped[Decimal] = mapped_column(
        Numeric(10, 3),
        nullable=False
    )

    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    adjusted_by_exec_id: Mapped[int] = mapped_column(
        ForeignKey("execs.exec_id"),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "amount_change <> 0",
            name="ck_adjustment_nonzero"
        ),
    )


class Payment(Base):
    __tablename__ = "payments"

    payment_id: Mapped[int] = mapped_column(
        primary_key=True
    )

    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.player_id"),
        nullable=False
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 3),
        nullable=False
    )

    paid_on: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    collected_by_exec_id: Mapped[int] = mapped_column(
        ForeignKey("execs.exec_id"),
        nullable=False
    )

    recorded_by_exec_id: Mapped[int] = mapped_column(
        ForeignKey("execs.exec_id"),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        nullable=False
    )

    method: Mapped[str] = mapped_column(
        String(20),
        server_default="cash",
        nullable=False
    )

    note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # Sent by the app with each new payment form, so submitting it twice records it once
    idempotency_key: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "amount > 0",
            name="ck_payment_positive"
        ),
        CheckConstraint(
            "status IN ('active', 'reversed')",
            name="ck_payment_status"
        ),
        CheckConstraint(
            "method IN ('cash', 'bank_transfer')",
            name="ck_payment_method"
        ),
        UniqueConstraint(
            "idempotency_key",
            name="uq_payments_idempotency_key"
        ),
    )


class PaymentAllocation(Base):
    __tablename__ = "payment_allocations"

    allocation_id: Mapped[int] = mapped_column(
        primary_key=True
    )

    payment_id: Mapped[int] = mapped_column(
        ForeignKey("payments.payment_id"),
        nullable=False
    )

    fee_month: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    amount_allocated: Mapped[Decimal] = mapped_column(
        Numeric(10, 3),
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "payment_id",
            "fee_month",
            name="uq_payment_month"
        ),
        CheckConstraint(
            "amount_allocated > 0",
            name="ck_allocation_positive"
        ),
    )


class Expense(Base):
    __tablename__ = "expenses"

    expense_id: Mapped[int] = mapped_column(
        primary_key=True
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 3),
        nullable=False
    )

    expense_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    paid_by_exec_id: Mapped[int] = mapped_column(
        ForeignKey("execs.exec_id"),
        nullable=False
    )

    recorded_by_exec_id: Mapped[int] = mapped_column(
        ForeignKey("execs.exec_id"),
        nullable=False
    )

    funding_source: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "amount > 0",
            name="ck_expense_positive"
        ),
        CheckConstraint(
            "funding_source IN ('club_funds', 'personal')",
            name="ck_expense_funding_source"
        ),
        CheckConstraint(
            "status IN ('active', 'reversed')",
            name="ck_expense_status"
        ),
    )


class Transfer(Base):
    __tablename__ = "transfers"

    transfer_id: Mapped[int] = mapped_column(
        primary_key=True
    )

    from_exec_id: Mapped[int] = mapped_column(
        ForeignKey("execs.exec_id"),
        nullable=False
    )

    to_exec_id: Mapped[int] = mapped_column(
        ForeignKey("execs.exec_id"),
        nullable=False
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 3),
        nullable=False
    )

    transferred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    recorded_by_exec_id: Mapped[int] = mapped_column(
        ForeignKey("execs.exec_id"),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "amount > 0",
            name="ck_transfer_positive"
        ),
        CheckConstraint(
            "from_exec_id <> to_exec_id",
            name="ck_transfer_different_execs"
        ),
        CheckConstraint(
            "status IN ('active', 'reversed')",
            name="ck_transfer_status"
        ),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    audit_id: Mapped[int] = mapped_column(
        primary_key=True
    )

    exec_id: Mapped[int] = mapped_column(
        ForeignKey("execs.exec_id"),
        nullable=False
    )

    action: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    table_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    record_id: Mapped[int] = mapped_column(
        nullable=False
    )

    old_values: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True
    )

    new_values: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "action IN ('CREATE', 'UPDATE', 'DELETE', 'REVERSE', 'FINALIZE')",
            name="ck_audit_action"
        ),
    )



class ExecOpeningBalance(Base):
    __tablename__ = "exec_opening_balances"

    # One row per Exec, so the Exec's id is also the primary key
    exec_id: Mapped[int] = mapped_column(
        ForeignKey("execs.exec_id"),
        primary_key=True
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 3),
        nullable=False
    )

    as_of: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    set_by_exec_id: Mapped[int] = mapped_column(
        ForeignKey("execs.exec_id"),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "amount >= 0",
            name="ck_exec_opening_balance_not_negative"
        ),
    )


class PlayerOpeningBalance(Base):
    __tablename__ = "player_opening_balances"

    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.player_id"),
        primary_key=True
    )

    # Positive: the player owed this much. Negative: the player had this much credit.
    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 3),
        nullable=False
    )

    as_of: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    set_by_exec_id: Mapped[int] = mapped_column(
        ForeignKey("execs.exec_id"),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )



class Income(Base):
    __tablename__ = "incomes"

    income_id: Mapped[int] = mapped_column(primary_key=True)

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 3),
        nullable=False
    )

    income_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    # The Exec who received the money, and now holds it
    received_by_exec_id: Mapped[int] = mapped_column(
        ForeignKey("execs.exec_id"),
        nullable=False
    )

    recorded_by_exec_id: Mapped[int] = mapped_column(
        ForeignKey("execs.exec_id"),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="active",
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "amount > 0",
            name="ck_income_positive"
        ),
        CheckConstraint(
            "status IN ('active', 'reversed')",
            name="ck_income_status"
        ),
    )
