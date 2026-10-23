from datetime import date
from pydantic import BaseModel, ConfigDict, Field


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