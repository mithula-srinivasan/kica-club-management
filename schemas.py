from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Literal


Gender = Literal["male", "female", "other"]


class PlayerDetails(BaseModel):
    """The details every player has. Shared by the exec "Add player" form and the public Join form."""
    # Required
    name: str = Field(min_length=1, max_length=100)
    phone_1: str = Field(min_length=1, max_length=30)
    email: EmailStr
    date_of_birth: date
    parent_name: str = Field(min_length=1, max_length=100)
    country: str = Field(min_length=1, max_length=100)
    gender: Gender

    # Optional
    phone_2: str | None = Field(default=None, max_length=30)
    fide_id: str | None = Field(default=None, max_length=20)




class PlayerCreate(PlayerDetails):
    # Execs also choose the joined date (the KICA ID is given automatically)
    joined_on: date


class RegistrationCreate(PlayerDetails):
    # The consent box on the Join form
    consent: bool

    # A hidden box people never see. Spam bots fill in every box, so if this
    # has anything in it, the "registration" came from a bot.
    website: str | None = None



class RegistrationResponse(BaseModel):
    registration_id: int
    name: str
    parent_name: str
    phone_1: str
    phone_2: str | None
    email: str
    date_of_birth: date
    country: str
    gender: str | None
    fide_id: str | None
    status: str
    submitted_at: datetime
    consented_at: datetime
    reviewed_at: datetime | None
    reviewed_by_name: str | None
    rejection_reason: str | None
    # Once approved: the player it became
    player_id: int | None
    kica_id: str | None


class RegistrationReject(BaseModel):
    reason: str = Field(min_length=1, max_length=500)

    

class PlayerResponse(BaseModel):
    player_id: int
    kica_id: str
    name: str
    joined_on: date | None
    is_active: bool
    phone_1: str
    phone_2: str | None
    email: str
    parent_name: str
    fide_id: str | None
    gender: str | None
    date_of_birth: date
    country: str

    model_config = ConfigDict(from_attributes=True)


class PlayerUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    joined_on: date | None = None
    phone_1: str | None = Field(default=None, max_length=30)
    phone_2: str | None = Field(default=None, max_length=30)
    email: EmailStr | None = None
    parent_name: str | None = Field(default=None, max_length=100)
    fide_id: str | None = Field(default=None, max_length=20)
    gender: Gender | None = None
    date_of_birth: date | None = None
    country: str | None = Field(default=None, max_length=100)


    
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
    collected_by_exec_id: int | None = None


class PaymentResponse(BaseModel):
    payment_id: int
    player_id: int
    player_name: str
    amount: Decimal
    paid_on: date
    method: str
    note: str | None
    status: str
    collected_by_exec_id: int
    collected_by_name: str
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
    is_opening_balance: bool = False


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
    paid_by_exec_id: int | None = None


class ExpenseResponse(BaseModel):
    expense_id: int
    description: str
    amount: Decimal
    expense_date: date
    status: str
    paid_by_exec_id: int
    paid_by_name: str
    recorded_by_exec_id: int
    recorded_by_name: str
    created_at: datetime


class ExpenseReverse(BaseModel):
    reason: str = Field(min_length=1, max_length=500)


class TransferCreate(BaseModel):
    from_exec_id: int
    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=3)
    transferred_on: date
    to_exec_id: int | None = None


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
    income_received: Decimal


class DashboardResponse(BaseModel):
    active_players: int
    club_balance: Decimal
    cash_held: list[ExecCashHeld]
    total_outstanding: Decimal
    players_owing: int
    total_credit: Decimal
    month: MonthSummary


class AuditLogResponse(BaseModel):
    audit_id: int
    exec_id: int
    exec_name: str
    action: str
    table_name: str
    record_id: int
    old_values: dict | None
    new_values: dict | None
    created_at: datetime



class ExecOpeningBalanceSet(BaseModel):
    amount: Decimal = Field(ge=0, max_digits=10, decimal_places=3)
    as_of: date


class PlayerOpeningBalanceSet(BaseModel):
    amount: Decimal = Field(max_digits=10, decimal_places=3)
    as_of: date


class ExecOpeningBalanceResponse(BaseModel):
    exec_id: int
    name: str
    amount: Decimal
    as_of: date
    set_by_name: str
    updated_at: datetime


class PlayerOpeningBalanceResponse(BaseModel):
    player_id: int
    player_name: str
    amount: Decimal
    as_of: date
    set_by_name: str
    updated_at: datetime


class OpeningBalancesResponse(BaseModel):
    execs: list[ExecOpeningBalanceResponse]
    players: list[PlayerOpeningBalanceResponse]


class SessionDateChange(BaseModel):
    session_date: date


class ExecAdminResponse(BaseModel):
    exec_id: int
    name: str
    email: str
    role: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class FeeRateCreate(BaseModel):
    monthly_amount: Decimal = Field(gt=0, max_digits=10, decimal_places=3)
    effective_from: date


class FeeRateResponse(BaseModel):
    fee_rate_id: int
    monthly_amount: Decimal
    effective_from: date
    changed_by_name: str | None


class IncomeCreate(BaseModel):
    description: str = Field(min_length=1, max_length=500)
    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=3)
    income_date: date
    received_by_exec_id: int | None = None


class IncomeResponse(BaseModel):
    income_id: int
    description: str
    amount: Decimal
    income_date: date
    status: str
    received_by_exec_id: int
    received_by_name: str
    recorded_by_exec_id: int
    recorded_by_name: str
    created_at: datetime


class IncomeReverse(BaseModel):
    reason: str = Field(min_length=1, max_length=500)



