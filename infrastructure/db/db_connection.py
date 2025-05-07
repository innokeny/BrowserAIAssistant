import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import redis
from contextlib import contextmanager

# PostgreSQL connection
POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'postgres')
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'pg_db')

# Redis connection
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = os.getenv('REDIS_PORT', '6379')
REDIS_DB = os.getenv('REDIS_DB', '0')

# PostgreSQL connection string
SQLALCHEMY_DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Create SQLAlchemy engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for declarative models
Base = declarative_base()

# Redis client
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=int(REDIS_PORT),
    db=int(REDIS_DB),
    decode_responses=True
)

@contextmanager
def get_db_session():
    """Provide a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def get_redis_client():
    """Get Redis client for caching and metrics storage."""
    return redis_client

def get_data_from_db():
    user = 'postgres' 
    password = 'postgres'  
    host = 'localhost'  
    port = '5432'  
    database = 'pg_db'  

    connection_string = f'postgresql://{user}:{password}@{host}:{port}/{database}'
    
    engine = create_engine(connection_string)

    query = """
        SELECT 
            w.start_date,
            w.end_date,
            e.event_name,
            w.event_intensity,
            r.region_name AS region,
            r.federal_district,
            (w.end_date - w.start_date) AS duration
        FROM 
            normalized_weather_events w
        JOIN 
            weather_events_types e ON w.event_id = e.event_id
        JOIN 
            weather_regions r ON w.region_id = r.region_id; 
    """
    
    df = pd.read_sql(query, engine)

    return df



