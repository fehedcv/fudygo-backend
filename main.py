#create the table
import logging
from sqlalchemy.exc import OperationalError

# Import models here to register them with the Base metadata
from app.models import user, restaurant

from app.db.base import Base
from app.db.session import engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

if __name__ == "__main__":
    create_tables(engine)
