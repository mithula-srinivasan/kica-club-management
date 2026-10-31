from fastapi import FastAPI
from routers import players, auth, execs, club_sessions, fees, payments, expenses, transfers, dashboard, audit_logs

app = FastAPI(title="KICA Club Management API")

app.include_router(players.router)
app.include_router(auth.router)
app.include_router(execs.router)
app.include_router(club_sessions.router)
app.include_router(fees.router)
app.include_router(payments.router)
app.include_router(expenses.router)
app.include_router(transfers.router)
app.include_router(dashboard.router)
app.include_router(audit_logs.router)

