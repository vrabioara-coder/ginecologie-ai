from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from db import SessionLocal, engine, create_db, User, MedicalProfile
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
import hashlib

# Crează baza de date dacă nu există
create_db()

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def hash_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "rezultat": None})


@app.post("/", response_class=HTMLResponse)
async def form(request: Request, saptamana: int = Form(...), simptome: str = Form(...)):
    from ai_module import get_ai_recommendation

    if not hasattr(app.state, "cache"):
        app.state.cache = {}
    key = f"{saptamana}-{simptome.lower()}"
    if key in app.state.cache:
        rezultat = app.state.cache[key]
    else:
        rezultat = get_ai_recommendation(saptamana, simptome)
        app.state.cache[key] = rezultat

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "rezultat": rezultat, "saptamana": saptamana, "simptome": simptome},
    )


@app.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@app.post("/signup")
def signup_action(
    request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)
):
    hashed_pw = hash_password(password)
    user = User(email=email, hashed_password=hashed_pw)
    db.add(user)
    db.commit()
    response = RedirectResponse(url="/login", status_code=302)
    return response


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
def login_action(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    hashed_pw = hash_password(password)
    user = db.query(User).filter(User.email == email, User.hashed_password == hashed_pw).first()
    if user:
        request.session["user_id"] = user.id
        return RedirectResponse(url="/profil", status_code=302)
    else:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Email sau parola incorectă"})


@app.get("/profil", response_class=HTMLResponse)
def profile_page(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login")

    profil = db.query(MedicalProfile).filter(MedicalProfile.user_id == user_id).first()
    return templates.TemplateResponse("profil.html", {"request": request, "profil": profil})


@app.post("/profil")
def profile_update(
    request: Request,
    db: Session = Depends(get_db),
    varsta: int = Form(None),
    inaltime: int = Form(None),
    greutate: int = Form(None),
    grupa_sange: str = Form(None),
    rh: str = Form(None),
    nr_sarcini: int = Form(None),
    nr_nasteri: int = Form(None),
    tip_nasteri: str = Form(None),
    avorturi: str = Form(None),
    dum: str = Form(None),
    dpn: str = Form(None),
    complicatii: str = Form(None),
    sarcina_risc: bool = Form(False),
    boli: str = Form(None),
    medicatie_sarcina: str = Form(None),
    alergii: str = Form(None),
    fumatoare: bool = Form(False),
    alcool: bool = Form(False)
):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login")

    profil = db.query(MedicalProfile).filter(MedicalProfile.user_id == user_id).first()
    if not profil:
        profil = MedicalProfile(user_id=user_id)

    profil.varsta = varsta
    profil.inaltime = inaltime
    profil.greutate = greutate
    profil.grupa_sange = grupa_sange
    profil.rh = rh
    profil.nr_sarcini = nr_sarcini
    profil.nr_nasteri = nr_nasteri
    profil.tip_nasteri = tip_nasteri
    profil.avorturi = avorturi
    profil.dum = dum
    profil.dpn = dpn
    profil.complicatii = complicatii
    profil.sarcina_risc = sarcina_risc
    profil.boli = boli
    profil.medicatie_sarcina = medicatie_sarcina
    profil.alergii = alergii
    profil.fumatoare = fumatoare
    profil.alcool = alcool

    db.add(profil)
    db.commit()
    return RedirectResponse(url="/profil", status_code=302)
