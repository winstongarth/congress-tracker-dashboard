from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import members, tickers, trades

app = FastAPI(
    title="Congress Portfolio Tracker API",
    description="Educational/informational only. Not investment advice. "
    "Disclosed amounts are ranges, not exact figures.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(trades.router)
app.include_router(members.router)
app.include_router(tickers.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
