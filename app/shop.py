from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlmodel import Session, select

from .db import get_session
from .models import Product, Purchase, User
from .auth import get_current_user
from .templating import templates            # było: .templates


router = APIRouter(prefix="/shop", tags=["shop"])

@router.get("/", response_class=HTMLResponse)
def shop_home(request: Request,
              user: User = Depends(get_current_user),
              session: Session = Depends(get_session)):
    products = session.exec(select(Product)).all()
    return templates.TemplateResponse(
        "shop.html",
        {"request": request, "user": user, "products": products}
    )


@router.post("/buy/{product_id}")
def buy_product(product_id: int,
                request: Request,
                session: Session = Depends(get_session)):
    user = get_current_user(request, session)
    if user is None:
        return RedirectResponse("/login?msg=login_required", status_code=303)

    product = session.get(Product, product_id)
    if product is None:
        return RedirectResponse("/shop?msg=no_item", status_code=303)

    if user.points < product.price:
        return RedirectResponse("/shop?msg=no_points", status_code=303)

    # zapobiegaj wielokrotnemu zakupowi tego samego przedmiotu
    already = session.exec(
        select(Purchase).where(
            Purchase.user_id == user.id,
            Purchase.product_id == product.id
        )
    ).first()
    if already:
        return RedirectResponse("/shop?msg=already_bought", status_code=303)

    # transakcja
    user.points -= product.price
    session.add_all([
        user,
        Purchase(user_id=user.id, product_id=product.id)
    ])
    session.commit()

    return RedirectResponse("/shop/secrets?msg=buy_ok", status_code=303)


@router.get("/secrets", response_class=HTMLResponse)
def my_secrets(request: Request,
               user: User = Depends(get_current_user),
               session: Session = Depends(get_session)):
    if user is None:
        return RedirectResponse("/login?msg=login_required", status_code=303)

    secrets_q = (session
        .exec(
            select(Product.name, Product.secret_text)
            .join(Purchase, Purchase.product_id == Product.id)
            .where(Purchase.user_id == user.id)
        )
        .all()
    )
    return templates.TemplateResponse(
        "secrets.html",
        {"request": request, "user": user, "secrets_q": secrets_q}
    )

