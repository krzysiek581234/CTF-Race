from fastapi import APIRouter, Depends, Form, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select
from jose import jwt, JWTError
from datetime import timedelta

from .db import get_session
from .models import User
from .utils import (
    generate_unique_activation_code,
    verify_password,
    hash_password,
    create_access_token,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

router = APIRouter()


# ---------- register ----------
@router.post("/register")
def register(
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session),
):
    # ---- WALIDACJA --------------------------------------------------------
    if session.exec(select(User).where(User.username == username)).first():
        return RedirectResponse("/register?msg=user_exists",
                                status_code=status.HTTP_303_SEE_OTHER)

    if "@" not in username or "." not in username.split("@")[-1]:
        return RedirectResponse("/register?msg=invalid_email",
                                status_code=status.HTTP_303_SEE_OTHER)

    if len(password) < 4:
        return RedirectResponse("/register?msg=password_short",
                                status_code=status.HTTP_303_SEE_OTHER)

    # ---- ZAPIS UŻYTKOWNIKA -----------------------------------------------
    code = generate_unique_activation_code(session)
    user = User(username=username, hashed_password=hash_password(password), activation_code=code)
    session.add(user)
    session.commit()

    # ---- AUTOMATYCZNE LOGOWANIE ------------------------------------------
    access_token = create_access_token(
        subject=user.username,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    resp = RedirectResponse("/?msg=register_ok",
                            status_code=status.HTTP_303_SEE_OTHER)
    resp.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
    )
    return resp


# ---------- login ----------
@router.post("/login")
def login(
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session),
):
    user = session.exec(select(User).where(User.username == username)).first()
    if not user or not verify_password(password, user.hashed_password):
        return RedirectResponse("/login?msg=invalid_credentials",
                                status_code=status.HTTP_303_SEE_OTHER)

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(subject=user.username,
                                       expires_delta=access_token_expires)

    response = RedirectResponse("/?msg=login_ok",
                                status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
    )
    return response


# ---------- logout ----------
@router.post("/logout")
async def logout(request: Request):
    response = RedirectResponse(
        url="/?msg=logout_ok",
        status_code=status.HTTP_303_SEE_OTHER
    )
    response.delete_cookie(key="access_token", httponly=True, samesite="lax")
    return response


# ---------- current user ----------
def get_current_user(request: Request, session: Session = Depends(get_session)):
    token: str | None = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
    except JWTError:
        return None
    if username is None:
        return None
    return session.exec(select(User).where(User.username == username)).first()
