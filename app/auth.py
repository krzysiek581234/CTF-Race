from fastapi import APIRouter, Depends, HTTPException, status, Form, Request, Response
from sqlmodel import Session, select
from jose import jwt, JWTError
from datetime import timedelta

from .db import get_session
from .models import User
from .schemas import UserCreate
from .utils import (
    verify_password,
    hash_password,
    create_access_token,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

router = APIRouter()

# -------- helper --------
def _username_exists(username: str, session: Session) -> bool:
    return session.exec(select(User).where(User.username == username)).first() is not None

# -------- register --------
@router.post("/register")
def register(
    username: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session),
):
    if _username_exists(username, session):
        raise HTTPException(status_code=400, detail="Użytkownik już istnieje.")
    user = User(username=username, hashed_password=hash_password(password))
    session.add(user)
    session.commit()
    return {"msg": "Rejestracja zakończona sukcesem."}

# -------- login --------
@router.post("/login")
def login(
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session),
):
    user = session.exec(select(User).where(User.username == username)).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Nieprawidłowe dane logowania.")
    access_token = create_access_token(subject=user.username)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
    )
    return {"msg": "Zalogowano pomyślnie."}

# -------- logout --------
@router.get("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"msg": "Wylogowano."}

# -------- current user dependency --------
def get_current_user(request: Request, session: Session = Depends(get_session)):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None
    return session.exec(select(User).where(User.username == username)).first()
