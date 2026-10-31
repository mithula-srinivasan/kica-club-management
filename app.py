from fastapi import FastAPI
from routers import players, auth, execs, club_sessions, fees

app = FastAPI(title="KICA Club Management API")

app.include_router(players.router)
app.include_router(auth.router)
app.include_router(execs.router)
app.include_router(club_sessions.router)
app.include_router(fees.router)

