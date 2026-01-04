from fastapi import FastAPI, Request, Form, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
from passlib.context import CryptContext
import sqlite3
import openai
import os
import json

openai.api_key = os.getenv("OPENAI_API_KEY")  # sau pune direct cheia aici (nu e recomandat pentru producție)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="supersecret123")
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")
pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")

DB_FILE = "ginecologie.db"

# ---------------- DB ----------------
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            nume TEXT,
            prenume TEXT,
            email TEXT
        )
    """)
    conn.commit()
    conn.close()
    print("Baza de date a fost creată!")

@app.on_event("startup")
def startup():
    create_tables()

# ---------------- Auth ----------------
# Hash parola
# Hash parola
def hash_password(password: str) -> str:
    return pwd_context.hash(password)  # Fără encode sau slice

# Verificare parola
def verify_password(plain_password, hashed_password) -> bool:
    return pwd_context.verify(plain_password, hashed_password)  # Fără encode sau slice

# ---------------- AI ----------------
import openai
import os
import json

openai.api_key = os.getenv("OPENAI_API_KEY")  # asigură-te că ai cheia setată

def generate_recommendations(simptome: str, saptamani_sarcina: int):
    """
    Generează recomandări pentru un pacient gravid.
    - 'urgent': rezumat al simptomelor + simptome care necesită mers la spital și 3 posibile diagnostice.
    - 'general': 5 recomandări generale în funcție de simptome și săptămânile de sarcină.
    """
    prompt = f"""
Ești un medic profesionist specializat în sarcină.
Pacientul are {saptamani_sarcina} săptămâni de sarcină și prezintă următoarele simptome: {simptome}.

Oferă recomandări structurate în două categorii:
1. Urgent:
   - Începe cu un mic rezumat al simptomelor și ce ar putea însemna ele.
   - Apoi listează 3 posibile diagnostice care necesită evaluare imediată la spital.
2. General: 5 recomandări generale pentru sănătatea în sarcină, ce poate face acasă pentru a se menține sănătoasă.

Răspunde STRICT în format JSON cu cheile:
{{
    "urgent": ["rezumat al simptomelor", "diagnostic + recomandare 1", "diagnostic + recomandare 2", "diagnostic + recomandare 3"],
    "general": ["sfat general 1", "sfat general 2", "sfat general 3", "sfat general 4", "sfat general 5"]
}}
"""

    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ești un asistent medical profesionist."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=700,
            temperature=0.7
        )

        text = response.choices[0].message.content

        # Încearcă să parsezi JSON-ul
        try:
            data = json.loads(text)
            urgent = data.get("urgent", [])
            general = data.get("general", [])
            return {"urgent": urgent, "general": general}
        except json.JSONDecodeError:
            return {"urgent": [], "general": [text]}
    except Exception as e:
        return {"urgent": [], "general": [f"Eroare la generarea recomandărilor: {e}"]}

# ---------------- Routes ----------------
@app.get("/")
def index(request: Request):
    profil = request.session.get("user")
    return templates.TemplateResponse("index.html", {"request": request, "profil": profil})

@app.get("/login")
def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "eroare": None})

@app.post("/login")
def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()

    if user and verify_password(password, user["password"]):
        request.session["user"] = {
            "username": user["username"],
            "nume": user["nume"],
            "prenume": user["prenume"],
            "email": user["email"]
        }
        return RedirectResponse("/profil", status_code=302)

    return templates.TemplateResponse("login.html", {"request": request, "eroare": "Date invalide"})

@app.get("/signup")
def signup_get(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request, "eroare": None})

@app.post("/signup")
def signup_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    nume: str = Form(...),
    prenume: str = Form(...),
    email: str = Form(...)
):
    try:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO users (username, password, nume, prenume, email) VALUES (?, ?, ?, ?, ?)",
            (username, hash_password(password), nume, prenume, email)
        )
        conn.commit()
        conn.close()
        return RedirectResponse("/login", status_code=302)
    except sqlite3.IntegrityError:
        return templates.TemplateResponse("signup.html", {"request": request, "eroare": "Username deja existent"})

@app.get("/profil")
def profil_get(request: Request):
    profil = request.session.get("user")
    if not profil:
        return RedirectResponse("/login", status_code=302)

    return templates.TemplateResponse(
        "profil.html",
        {"request": request, "profil": profil, "recomandari": None}
    )

@app.post("/profil")
async def profil_post(request: Request):
    profil = request.session.get("user")
    if not profil:
        return RedirectResponse("/login", status_code=302)

    form = await request.form()

    # Preluare date complet profil
    nume = form.get("nume", profil["nume"])
    prenume = form.get("prenume", profil["prenume"])
    email = form.get("email", profil["email"])
    simptome = form.get("simptome", "").strip()
    
    # Preluare număr săptămâni de sarcină
    try:
        saptamani_sarcina = int(form.get("saptamani_sarcina", "0"))
    except ValueError:
        saptamani_sarcina = 0

    # Salvează datele în DB
    username = profil["username"]
    conn = get_db_connection()
    conn.execute(
        "UPDATE users SET nume = ?, prenume = ?, email = ? WHERE username = ?",
        (nume, prenume, email, username)
    )
    conn.commit()
    conn.close()

    # Actualizează sesiunea
    request.session["user"] = {
        "username": username,
        "nume": nume,
        "prenume": prenume,
        "email": email
    }

    # Generează recomandări AI dacă sunt simptome
    recomandari = generate_recommendations(simptome, saptamani_sarcina) if simptome else None

    return templates.TemplateResponse(
        "profil.html",
        {
            "request": request,
            "profil": request.session["user"],
            "recomandari": recomandari
        }
    )
@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)
