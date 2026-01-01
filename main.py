from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from ai_module import get_ai_recommendation

app = FastAPI()

# Templates
templates = Jinja2Templates(directory="templates")

# Static files (CSS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Home page
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "rezultat": None
        }
    )

# Form submit
@app.post("/", response_class=HTMLResponse)
async def form(request: Request):
    form = await request.form()
    saptamana = form.get("saptamana")
    simptome = form.get("simptome")

    # Inițializare cache
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
        {
            "request": request,
            "rezultat": rezultat,
            "saptamana": saptamana,
            "simptome": simptome
        }
    )
