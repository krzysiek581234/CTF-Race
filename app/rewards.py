# app/rewards.py  –  WERSJA *PODATNA*
from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse
from sqlmodel import Session
from sqlalchemy import text
from .db import get_session
from .models import User
from .auth import get_current_user
import asyncio

router = APIRouter()

@router.post("/redeem")
async def redeem_points(
    request: Request,
    code: str = Form(...),
    session: Session = Depends(get_session),
):
    user: User | None = get_current_user(request, session)
    if user is None:
        return RedirectResponse("/login?msg=login_required",
                                status_code=status.HTTP_303_SEE_OTHER)

    # logika kontrolna PRZED transakcją – zostawiamy
    if user.code_redeemed:
        return RedirectResponse("/?msg=already_redeemed",
                                status_code=status.HTTP_303_SEE_OTHER)
    if code != user.activation_code:
        return RedirectResponse("/?msg=wrong_code",
                                status_code=status.HTTP_303_SEE_OTHER)

    # -------------- OKNO WYŚCIGU 1 --------------
    await asyncio.sleep(0.4)               # celowe opóźnienie

    # (A) podbij punkty – BEZ zmiany flagi
    session.exec(
        text("UPDATE user SET points = points + 10 WHERE id = :uid")
        .bindparams(uid=user.id)
    )
    session.commit()                       # pierwszy commit
    await asyncio.sleep(0)                 # oddaj sterowanie

    # -------------- OKNO WYŚCIGU 2 --------------
    await asyncio.sleep(0.4)               # drugie okno

    # (B) dopiero teraz ustaw flagę
    session.exec(
        text("UPDATE user SET code_redeemed = 1 WHERE id = :uid")
        .bindparams(uid=user.id)
    )
    session.commit()                       # drugi commit

    return RedirectResponse("/?msg=redeem_ok", status_code=303)
