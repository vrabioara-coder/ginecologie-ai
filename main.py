from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ai_module import get_ai_recommendation
from db import SessionLocal, User

import os
from fastapi.templating import Jinja2Templates

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # directorul unde se află main.py
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

app = FastAPI()


# Dependency pentru DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------
# HOME / FORMULAR AI
# -------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "rezultat": None})

@app.post("/", response_class=HTMLResponse)
async def form(request: Request, db: Session = Depends(get_db)):
    user_email = request.cookies.get("user_email")
    if not user_email:
        return RedirectResponse("/login")

    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        return RedirectResponse("/login")

    # verifică cereri gratuite
    if user.plan == "free" and user.cereri_ramase <= 0:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "error": "Ai epuizat cererile gratuite. Apasă Upgrade la Premium pentru acces nelimitat.",
                "rezultat": None
            }
        )

    form_data = await request.form()
    saptamana = form_data.get("saptamana")
    simptome = form_data.get("simptome")

    # CACHE AI
    if not hasattr(app.state, "cache"):
        app.state.cache = {}
    key = f"{saptamana}-{simptome.lower()}"
    if key in app.state.cache:
        rezultat = app.state.cache[key]
    else:
        rezultat = get_ai_recommendation(saptamana, simptome)
        app.state.cache[key] = rezultat

    # decrement cereri gratuite
    if user.plan == "free":
        user.cereri_ramase -= 1
        db.commit()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "rezultat": rezultat,
            "saptamana": saptamana,
            "simptome": simptome
        }
    )

# -------------------------
# SIGNUP
# -------------------------
@app.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/signup")
async def signup(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    email = form.get("email")
    password = form.get("password")  # atenție: hashing recomandat

    if db.query(User).filter(User.email == email).first():
        return templates.TemplateResponse("signup.html", {"request": request, "error": "Email deja folosit."})

    user = User(email=email, password_hash=password, plan="free", cereri_ramase=20)
    db.add(user)
    db.commit()
    response = RedirectResponse("/", status_code=302)
    response.set_cookie("user_email", email)
    return response

# -------------------------
# LOGIN
# -------------------------
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    email = form.get("email")
    password = form.get("password")

    user = db.query(User).filter(User.email == email).first()
    if not user or user.password_hash != password:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Email sau parolă incorectă."})

    response = RedirectResponse("/", status_code=302)
    response.set_cookie("user_email", email)
    return response

# -------------------------
# UPGRADE PREMIUM
# -------------------------
import hashlib

MERCHANT_ID = "TEST_MERCHANT"
SECRET_KEY = "SECRET_KEY"

@app.post("/upgrade")
async def upgrade(request: Request, db: Session = Depends(get_db)):
    user_email = request.cookies.get("user_email")
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        return RedirectResponse("/login")
    
    # exemplu link Netopia
    amount = 10.0
    data = f"{MERCHANT_ID}:{amount}:{SECRET_KEY}"
    signature = hashlib.sha256(data.encode()).hexdigest()
    payment_url = f"https://secure.mobilpay.ro/payment?merchant={MERCHANT_ID}&amount={amount}&sig={signature}"
    
    return RedirectResponse(payment_url)

@app.post("/webhook")
async def webhook(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    email = form.get("email")  # trimis de Netopia
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.plan = "premium"
        db.commit()
    return {"status": "ok"}
