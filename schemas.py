from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Literal


class PlayerCreate(BaseModel):
    kica_id: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=100)
    joined_on: date


class PlayerResponse(BaseModel):
    player_id: int
    kica_id: str | None
    name: str
    joined_on: date | None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class PlayerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    kica_id: str | None = Field(default=None, min_length=1, max_length=20)
    joined_on: date | None = None


class LoginRequest(BaseModel):
    email: str
    password: str
    remember_me: bool = False


class ExecResponse(BaseModel):
    exec_id: int
    name: str
    email: str
    role: str

    model_config = ConfigDict(from_attributes=True)



class PasswordSetupLinkRequest(BaseModel):
    exec_id: int


class PasswordSetupLinkResponse(BaseModel):
    exec_name: str
    setup_link: str
    expires_at: datetime


class SignupRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=12, max_length=128)


class SessionCreate(BaseModel):
    session_date: date


class SessionResponse(BaseModel):
    session_id: int
    session_date: date
    present_count: int


class AttendancePlayer(BaseModel):
    player_id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class SessionDetailResponse(BaseModel):
    session_id: int
    session_date: date
    present_players: list[AttendancePlayer]


class AttendanceUpdate(BaseModel):
    player_ids: list[int]



class MonthlyFeeResponse(BaseModel):
    player_id: int
    player_name: str
    fee_month: date
    base_fee: Decimal
    adjustments: Decimal
    amount_due: Decimal


class FeeAdjustmentCreate(BaseModel):
    player_id: int
    fee_month: date
    amount_change: Decimal = Field(max_digits=10, decimal_places=3)
    reason: str = Field(min_length=1, max_length=500)


class PaymentCreate(BaseModel):
    player_id: int
    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=3)
    paid_on: date
    method: Literal["cash", "bank_transfer"]
    note: str | None = Field(default=None, max_length=500)
    idempotency_key: str | None = Field(default=None, max_length=64)


class PaymentResponse(BaseModel):
    payment_id: int
    player_id: int
    player_name: str
    amount: Decimal
    paid_on: date
    method: str
    note: str | None
    status: str
    recorded_by_exec_id: int
    recorded_by_name: str
    created_at: datetime


class PaymentReverse(BaseModel):
    reason: str = Field(min_length=1, max_length=500)



class StatementMonth(BaseModel):
    fee_month: date
    amount_due: Decimal
    amount_paid: Decimal
    remaining: Decimal


class PlayerStatement(BaseModel):
    player_id: int
    player_name: str
    total_due: Decimal
    total_paid: Decimal
    outstanding: Decimal
    credit: Decimal
    months: list[StatementMonth]



class ExpenseCreate(BaseModel):
    description: str = Field(min_length=1, max_length=500)
    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=3)
    expense_date: date


class ExpenseResponse(BaseModel):
    expense_id: int
    description: str
    amount: Decimal
    expense_date: date
    status: str
    recorded_by_exec_id: int
    recorded_by_name: str
    created_at: datetime


class ExpenseReverse(BaseModel):
    reason: str = Field(min_length=1, max_length=500)


class TransferCreate(BaseModel):
    from_exec_id: int
    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=3)
    transferred_on: date


class TransferResponse(BaseModel):
    transfer_id: int
    from_exec_id: int
    from_exec_name: str
    to_exec_id: int
    to_exec_name: str
    amount: Decimal
    transferred_on: date
    status: str
    recorded_by_exec_id: int
    recorded_by_name: str
    created_at: datetime


class TransferReverse(BaseModel):
    reason: str = Field(min_length=1, max_length=500)


class ExecOption(BaseModel):
    exec_id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class ExecCashHeld(BaseModel):
    exec_id: int
    name: str
    amount: Decimal


class PlayerOutstanding(BaseModel):
    player_id: int
    player_name: str
    outstanding: Decimal


class MonthSummary(BaseModel):
    month: date
    sessions_held: int
    players_attended: int
    fees_assessed: Decimal
    payments_received: Decimal
    expenses_paid: Decimal


class DashboardResponse(BaseModel):
    active_players: int
    club_balance: Decimal
    cash_held: list[ExecCashHeld]
    total_outstanding: Decimal
    players_owing: int
    total_credit: Decimal
    month: MonthSummary