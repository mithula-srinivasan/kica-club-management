from dotenv import load_dotenv

# Read settings such as the Gmail details from a private .env file, if there is one
load_dotenv()

from fastapi import FastAPI
from routers import players, auth, execs, club_sessions, fees, payments, expenses, transfers, dashboard, audit_logs, opening_balances, exports, income

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
app.include_router(opening_balances.router)
app.include_router(exports.router)
app.include_router(income.router)
