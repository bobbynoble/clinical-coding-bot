from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os

from app.coder import suggest_codes

app = FastAPI(title="Clinical Coding Bot")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "templates")), name="static")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/suggest")
async def suggest(
    note: str = Form(...),
    systems: str = Form(default=""),
):
    selected_systems = [s.strip() for s in systems.split(",") if s.strip()] or None
    try:
        result = suggest_codes(note, systems=selected_systems)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/health")
async def health():
    return {"status": "ok"}
