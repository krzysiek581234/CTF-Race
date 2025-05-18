from fastapi import FastAPI, Request, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from sqlmodel import Session, select

from .db import init_db, get_session
from .auth import router as auth_router, get_current_user
from .models import Product

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="MiniShop SQL")

# Static & Templates
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# Startup
@app.on_event("startup")
def on_startup():
    init_db()

# Include auth routes
app.include_router(auth_router)

# ---- routes ----
@app.get("/", response_class=HTMLResponse)
def home(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("index.html", {"request": request, "user": user})

@app.get("/products", response_class=HTMLResponse)
def products(
    request: Request,
    user=Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if user is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    products = session.exec(select(Product)).all()
    return templates.TemplateResponse(
        "products.html",
        {"request": request, "user": user, "products": products},
    )
