from sqlalchemy.orm import Session
from app.models import Usage, User

def log_usage(db: Session, user_id: int, provider: str, model: str, usage: dict, ms: int, error: str | None = None):
    pt = int(usage.get("prompt_tokens") or 0)
    ct = int(usage.get("completion_tokens") or 0)
    tt = int(usage.get("total_tokens") or (pt + ct))
    # Cost estimation can be refined per-model; leaving 0.0 as placeholder
    row = Usage(
        user_id=user_id,
        provider=provider,
        model=model,
        prompt_tokens=pt,
        completion_tokens=ct,
        total_tokens=tt,
        cost_estimated=0.0,
        ms=ms,
        error=error,
    )
    db.add(row)
    db.commit()
