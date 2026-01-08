from dotenv import load_dotenv
load_dotenv()

from app.core.firebase import init_firebase
init_firebase()

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError

from app.db.base import Base
from app.db.session import engine
from app.api.v2.router import router as api_router
from app.realtime.orders_ws import router as ws_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ ONLY FastAPI app
app = FastAPI(
    title="FudyGo Backend API",
    description="API for a food delivery service.",
    version="2.0.0",
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "https://localhost",
        "http://localhost",
        "https://fudygo.tech",
        "https://pos.fudygo.tech",
    ],
    # stateless token-based auth; do not allow cookies/credentials
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(api_router)
app.include_router(ws_router)

@app.on_event("startup")
def on_startup():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database ready")
    except OperationalError as e:
        logger.error(e)

@app.get("/")
def root():
    return {"message": "Welcome to Fudygo API"}
