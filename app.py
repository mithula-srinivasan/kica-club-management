from fastapi import FastAPI
from routers import players

app = FastAPI(title="KICA Club Management API")

app.include_router(players.router)