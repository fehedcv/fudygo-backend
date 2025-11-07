import uvicorn
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import firebase core module to initialize firebase admin sdk
from app.core import firebase

#create the table
import logging
from sqlalchemy.exc import OperationalError
from fastapi import FastAPI, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Import models here to register them with the Base metadata
from app.models import user, restaurant

from app.api.v1 import user as user_api, restaurant as restaurant_api
from app.api.v1.admin import adminOps as admin_restaurant_api
from app.db.base import Base
from app.db.session import engine


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

security = HTTPBearer()

app = FastAPI(
    title="Elamfood API",
    description="API for a food delivery service.",
    version="1.0.0"
)

@app.on_event("startup")
def on_startup():
    create_tables(engine)

app.include_router(user_api.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(restaurant_api.router, prefix="/api/v1/restaurants", tags=["Restaurants"])
app.include_router(admin_restaurant_api.router, prefix="/api/v1/adm", tags=["Admin Restaurants"])


def create_tables(engine):
    try:
        logger.info("Attempting to create tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Tables created successfully.")
    except OperationalError as e:
        logger.error("Could not connect to the database. Please check your connection details and ensure the database exists.")
        logger.error(f"Error details: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

@app.get("/")
def read_root():
    return {"message": "Welcome to Fudygo API"}


if __name__ == "__main__":
    create_tables(engine)
    uvicorn.run(app, host="0.0.0.0", port=8000)
