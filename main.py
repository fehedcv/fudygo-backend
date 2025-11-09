import uvicorn
from dotenv import load_dotenv
load_dotenv()
import os
from app.core import firebase
# Load environment variables from .env file

# Check for Firebase service account JSON
'''if not os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON"):
    raise ValueError("FIREBASE_SERVICE_ACCOUNT_JSON environment variable not set. Please create a .env file and add the required environment variables.")
'''


import logging
from sqlalchemy.exc import OperationalError
from app.db.base import Base
from app.db.session import engine
from app.api.v2 import router
from fastapi.security import HTTPBearer

app = router.app
security = HTTPBearer()
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("startup")
def on_startup():
    create_tables(engine)

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
