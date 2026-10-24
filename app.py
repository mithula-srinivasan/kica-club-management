from fastapi import FastAPI
from routers import players, auth, execs

app = FastAPI(title="KICA Club Management API")

app.include_router(players.router)
app.include_router(auth.router)
app.include_router(execs.router)

