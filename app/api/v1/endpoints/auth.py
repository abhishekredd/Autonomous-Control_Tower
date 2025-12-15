# app/api/v1/endpoints/auth.py
from fastapi import APIRouter, HTTPException
from datetime import timedelta
from app.core.security import create_access_token, verify_password, get_password_hash
from app.core.config import settings

router = APIRouter()

# Dev-only: simple login. Replace with DB validation in production.
@router.post("/login")
def login(username: str = "admin", password: str = "admin"):
    # Example hardcoded dev creds; change or validate via DB
    if not (username == "admin" and password == "admin"):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token(
        {"sub": username, "role": "admin"},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": token, "token_type": "bearer"}
