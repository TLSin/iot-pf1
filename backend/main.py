from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.auth.signup import router as signup_router
from routers.auth.login import router as login_router
from routers.auth.logout import router as logout_router
from routers.dashboard import router as dashboard_router
from routers.users import router as users_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(signup_router, prefix="/auth/signup", tags=["auth"])
app.include_router(login_router, prefix="/auth/login", tags=["auth"])
app.include_router(logout_router, prefix="/auth/logout", tags=["auth"])
app.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
app.include_router(users_router, tags=["users"])

@app.get("/")
def read_root():
    return {"Hello": "World"}
