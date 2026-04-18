from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()

# 1. Create the csv directory if it doesn't exist
if not os.path.exists("csv"):
    os.makedirs("csv")

# 2. Mount the CSV folder so the browser can reach http://your-ip:8000/csv/temp.csv
app.mount("/csv", StaticFiles(directory="csv"), name="csv")

# 3. Mount the Root folder so the browser can find jsFuns.js, etc.
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    # This serves the index.html file we are about to create
    with open("index.html", "r") as f:
        return f.read()

@app.post("/event")
async def receive_event(request: Request):
    data = await request.json()
    with open("data.csv", "a") as f:
        f.write(f"{data.get('name')},{data.get('value')}\n")
    return {"status": "success"}