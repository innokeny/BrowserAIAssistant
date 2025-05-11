import os
import sys
import time
from sqlalchemy.exc import OperationalError
from infrastructure.db.db_connection import engine, Base

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

def init_db():
    """Initialize the database by creating all tables."""
    print("Creating database tables...")
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully!")
    except Exception as e:
        print(f"Error creating database tables: {e}")
        sys.exit(1)

def wait_for_db(max_retries=5, retry_interval=2):
    """Wait for the database to be ready."""
    retries = 0
    while retries < max_retries:
        try:
            # Try to connect to the database
            engine.connect()
            print("Database connection successful!")
            return True
        except OperationalError:
            retries += 1
            print(f"Database not ready yet. Retrying in {retry_interval} seconds... ({retries}/{max_retries})")
            time.sleep(retry_interval)
    
    print("Failed to connect to the database after multiple retries.")
    return False

def drop_db():
    """Drop all tables in the database."""
    print("Dropping all database tables...")
    try:
        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        print("All database tables dropped successfully!")
    except Exception as e:
        print(f"Error dropping database tables: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Wait for the database to be ready
    if wait_for_db():
        # drop_db()
        init_db()
    else:
        sys.exit(1) 