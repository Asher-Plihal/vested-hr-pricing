from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routers import clients, config, calculate

app = FastAPI(title="VestedHR Pricing Tool")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(clients.router)
app.include_router(config.router)
app.include_router(calculate.router)
