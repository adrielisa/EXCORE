from fastapi import FastAPI
from api import upload, optimize, results, health

app = FastAPI()

app.include_router(upload.router)
app.include_router(optimize.router)
app.include_router(results.router)
app.include_router(health.router)
