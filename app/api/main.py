from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import members, tickers, trades
from app.graphql.router import graphql_router
from config.settings import settings

app = FastAPI(
    title="Congress Portfolio Tracker API",
    description="Educational/informational only. Not investment advice. "
    "Disclosed amounts are ranges, not exact figures.",
)

# GraphQL needs POST in addition to the GET the REST routes use.
# In debug mode, also allow any http://localhost / LAN-IP origin+port so the
# Expo dev client (Metro on a random port, reached from a physical phone over
# the LAN) can call /graphql -- see "Mobile dev" in the README.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_origin_regex=(
        r"http://(localhost|127\.0\.0\.1|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}):\d+"
        if settings.debug
        else None
    ),
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(trades.router)
app.include_router(members.router)
app.include_router(tickers.router)
app.include_router(graphql_router, prefix="/graphql")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
