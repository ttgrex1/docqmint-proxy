from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import EmailStr

from app.config import settings
from app.db import Base, engine, get_db
from app.models import User, Usage, SettingsKV
from app.schemas import LoginRequest, TokenResponse, MeResponse, ChatRequest, UsageRow, SettingsUpdate
from app.auth import create_token, verify_password, hash_password, get_current_user, require_admin
from app.providers.openrouter import OpenRouterClient
from app.usage import log_usage

app = FastAPI(title="DocQmint Proxy", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.CORS_ORIGINS == "*" else settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables
Base.metadata.create_all(bind=engine)

# Seed admin
with next(get_db()) as db:
    if not db.query(User).filter(User.email == settings.ADMIN_EMAIL).first():
        admin = User(email=settings.ADMIN_EMAIL, password_hash=hash_password(settings.ADMIN_PASSWORD), role="admin")
        db.add(admin)
        db.commit()

@app.get("/health")
async def health():
    return {"ok": True}

@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(user.email, settings.JWT_EXPIRES_MIN)
    return {"token": token}

@app.get("/me", response_model=MeResponse)
def me(user: User = Depends(get_current_user)):
    return {"email": user.email, "role": user.role}

# Simple user create (admin)
@app.post("/admin/users")
def create_user(email: EmailStr, password: str, role: str = "user", user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_admin(user)
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="User exists")
    u = User(email=email, password_hash=hash_password(password), role=role)
    db.add(u)
    db.commit()
    return {"ok": True}

# Settings helpers
def get_setting(db: Session, key: str, default: str) -> str:
    row = db.query(SettingsKV).filter(SettingsKV.key == key).first()
    return row.value if row else default

def set_setting(db: Session, key: str, value: str):
    row = db.query(SettingsKV).filter(SettingsKV.key == key).first()
    if row:
        row.value = value
    else:
        row = SettingsKV(key=key, value=value)
        db.add(row)
    db.commit()

@app.get("/admin/settings")
def get_settings(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_admin(user)
    return {
        "default_model": get_setting(db, "default_model", settings.DEFAULT_MODEL),
        "temperature": float(get_setting(db, "temperature", str(settings.TEMPERATURE))),
        "max_tokens": int(get_setting(db, "max_tokens", str(settings.MAX_TOKENS))),
        "provider": settings.PROVIDER,
    }

@app.post("/admin/settings")
def update_settings(body: SettingsUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_admin(user)
    if body.default_model is not None:
        set_setting(db, "default_model", body.default_model)
    if body.temperature is not None:
        set_setting(db, "temperature", str(body.temperature))
    if body.max_tokens is not None:
        set_setting(db, "max_tokens", str(body.max_tokens))
    return {"ok": True}

# Chat proxy
@app.post("/chat/completions")
async def chat(body: ChatRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    model = body.model or get_setting(db, "default_model", settings.DEFAULT_MODEL)
    temperature = body.temperature if body.temperature is not None else float(get_setting(db, "temperature", str(settings.TEMPERATURE)))
    max_tokens = body.max_tokens if body.max_tokens is not None else int(get_setting(db, "max_tokens", str(settings.MAX_TOKENS)))

    payload = {
        "model": model,
        "messages": body.messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    provider = settings.PROVIDER
    error = None
    usage = {}
    ms = 0
    data = {}
    try:
        if provider == "openrouter":
            client = OpenRouterClient()
            data, meta = await client.chat_completions(payload)
            ms = meta["ms"]
            usage = meta.get("usage") or {}
        else:
            raise HTTPException(status_code=500, detail="Unsupported provider")
    except Exception as e:
        error = str(e)
        log_usage(db, user.id, provider, model, usage, ms, error=error)
        raise

    log_usage(db, user.id, provider, model, usage, ms, error=None)
    return data

# Admin usage export (JSON rows; clients can turn into CSV)
@app.get("/admin/usage", response_model=list[UsageRow])
def usage_export(
    from_: Optional[str] = Query(None, alias="from"),
    to: Optional[str] = None,
    user_email: Optional[EmailStr] = Query(None, alias="user"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_admin(user)
    q = db.query(Usage, User).join(User, User.id == Usage.user_id)
    if user_email:
        q = q.filter(User.email == user_email)
    if from_:
        q = q.filter(Usage.created_at >= from_)
    if to:
        q = q.filter(Usage.created_at <= to)
    rows = []
    for u, usr in q.order_by(Usage.created_at.desc()).all():
        rows.append({
            "user": usr.email,
            "provider": u.provider,
            "model": u.model,
            "prompt_tokens": u.prompt_tokens,
            "completion_tokens": u.completion_tokens,
            "total_tokens": u.total_tokens,
            "cost_estimated": u.cost_estimated,
            "ms": u.ms,
            "created_at": u.created_at.isoformat() if u.created_at else "",
        })
    return rows
