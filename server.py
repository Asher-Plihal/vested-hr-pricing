from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from controllers import clients, config, calculate, workers_comp, taxes

app = FastAPI(title="VestedHR Pricing Tool")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(clients.router)
app.include_router(config.router)
app.include_router(calculate.router)
app.include_router(workers_comp.router)
app.include_router(taxes.router)
