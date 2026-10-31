from datetime import date, datetime
from pydantic import BaseModel, EmailStr, ConfigDict, Field


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