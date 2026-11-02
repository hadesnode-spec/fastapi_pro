

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker 
import sqlalchemy
import redis
from app.config import settings
Base = declarative_base()
db_url= 'postgresql://postgres:112002@localhost:5432/fastapi_pro'
engine=create_engine(db_url)
SessionLocal = sessionmaker(bind=engine)
redis_client = redis.Redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2,
)



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_redis() -> redis.Redis:
    return redis_client