from pydantic import BaseModel, EmailStr
from typing import Optional, List

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    token: str

class MeResponse(BaseModel):
    email: EmailStr
    role: str

class ChatRequest(BaseModel):
    messages: list
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None

class UsageRow(BaseModel):
    user: str
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_estimated: float
    ms: int
    created_at: str

class SettingsUpdate(BaseModel):
    default_model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
