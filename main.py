from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount("/csv", StaticFiles(directory="dashboard/csv"), name="csv")
app.mount("/static", StaticFiles(directory="dashboard/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    with open("dashboard/index.html", "r") as f:
        return f.read()

