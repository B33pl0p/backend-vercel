from fastapi import FastAPI, Depends, Query
from sqlalchemy import create_engine, Column, Integer, String, Float, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# FastAPI app
app = FastAPI()

# Database Configuration
#DB_HOST = "localhost"
#for db in aws
DB_HOST= "database-products.c9kqgsu44jjh.eu-north-1.rds.amazonaws.com"
DB_PORT = "5432"
DB_USER = "postgres"

#DB_PASSWORD = "7878"
#for db in aws
DB_PASSWORD = "biplop123bB#"
DB_NAME = "products_db"

# Create the engine using host configuration
engine = create_engine(
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# SQLAlchemy Base Model
Base = declarative_base()

# Product Model
class Product(Base):
    __tablename__ = "products"
    product_id = Column(Integer, primary_key=True, index=True)
    gender = Column(String)
    master_category = Column(String)
    sub_category = Column(String)
    article_type = Column(String)
    base_colour = Column(String)
    season = Column(String)
    year = Column(Integer)
    product_display_name = Column(String)
    image_data = Column(LargeBinary)  # New: Store image file as BLOB
    price = Column(Float)
    rating = Column(Float)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
