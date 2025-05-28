from fastapi import FastAPI, Request, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
# from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from sqlmodel import Session, select

from .db import init_db, get_session
from .auth import router as auth_router, get_current_user
from .models import Product
from .rewards import router as rewards_router
from .templating import templates         
from .shop import router as shop_router

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="MiniShop SQL")

# Static & Templates
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
# templates = Jinja2Templates(directory=BASE_DIR / "templates")

# Startup
@app.on_event("startup")
def on_startup():
    init_db()

# Include auth routes
app.include_router(auth_router)
app.include_router(rewards_router) 
app.include_router(shop_router)
# ---- routes ----
@app.get("/", response_class=HTMLResponse)
def home(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse("index.html", {"request": request, "user": user})

@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_get(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

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
