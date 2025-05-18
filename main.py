from fastapi import FastAPI, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Dict, Optional

app = FastAPI(title="MiniShop")

# Static & Templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# JWT konfiguracja
SECRET_KEY = "CHANGE_ME_TO_SECRET_KEY"  # ← podmień na losowy, silny klucz
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Hashowanie haseł
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# "Baza" danych w pamięci (na start wystarczy)
fake_users_db: Dict[str, Dict[str, str]] = {}
fake_products_db = [
    {"id": 1, "name": "Laptop", "description": "Ultralekki laptop", "price": 3999},
    {"id": 2, "name": "Smartphone", "description": "Flagowy telefon", "price": 2999},
    {"id": 3, "name": "Słuchawki", "description": "Bezprzewodowe słuchawki", "price": 599},
]

# -------------- Pomocnicze --------------
def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(request: Request) -> Optional[Dict[str, str]]:
    """Zwraca słownik użytkownika lub None."""
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return fake_users_db.get(username)
    except JWTError:
        return None

# -------------- Routy publiczne --------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = get_current_user(request)
    return templates.TemplateResponse("index.html", {"request": request, "user": user})

@app.get("/register", response_class=HTMLResponse)
async def register_get(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register_post(username: str = Form(...), password: str = Form(...)):
    if username in fake_users_db:
        raise HTTPException(status_code=400, detail="Użytkownik już istnieje.")
    fake_users_db[username] = {
        "username": username,
        "hashed_password": hash_password(password),
    }
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login_post(username: str = Form(...), password: str = Form(...)):
    user = fake_users_db.get(username)
    if not user or not verify_password(password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Nieprawidłowe dane logowania.")
    access_token = create_access_token(data={"sub": username})
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
    )
    return response

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("access_token")
    return response

# -------------- Routy chronione --------------
@app.get("/products", response_class=HTMLResponse)
async def products(request: Request):
    user = get_current_user(request)
    if user is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(
        "products.html",
        {"request": request, "products": fake_products_db, "user": user},
    )
