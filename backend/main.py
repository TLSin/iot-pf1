from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from deps.rate_limit import limiter
from routers.auth.signup import router as signup_router
from routers.auth.login import router as login_router
from routers.auth.logout import router as logout_router
from routers.dashboard import router as dashboard_router
from routers.users import router as users_router
from routers.scan_card import router as scan_card_router

app = FastAPI()

# ─── Rate limiting ────────────────────────────────────────────────────────────
# Attach the SlowAPI limiter to the app state so it can intercept requests.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(signup_router, prefix="/auth/signup", tags=["auth"])
app.include_router(login_router, prefix="/auth/login", tags=["auth"])
app.include_router(logout_router, prefix="/auth/logout", tags=["auth"])
app.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
app.include_router(users_router, tags=["users"])

# RFID scan validation & registration (HTTP endpoints for scan.py + WebSocket for Vue)
app.include_router(scan_card_router, prefix="/scan-card", tags=["scan-card"])

# WebSocket endpoint lives at /ws/scan
# scan_card_router has the @router.websocket("/scan") defined,
# so we mount the router a second time under /ws to expose it there.
from routers.scan_card import router as ws_router
app.include_router(ws_router, prefix="/ws", tags=["websocket"])


@app.get("/")
def read_root():
    return {"Hello": "World"}
