from sqlalchemy import create_engine 
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker 

from .config import get_settings

engine = create_engine(
    get_settings().db_url, connect_args={"check_same_thread": False}
)

# engine.execute("alter table urls add column request_time TIMESTAMP default '2018-06-14 22:00:00';")

SessionLocal= sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)
Base = declarative_base()