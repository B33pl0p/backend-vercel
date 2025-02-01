from fastapi import FastAPI, Depends, Query
from sqlalchemy import create_engine, Column, Integer, String, Float, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# FastAPI app
app = FastAPI()

# Database Configuration (Amazon RDS)
DB_HOST = "database-products.c9kqgsu44jjh.eu-north-1.rds.amazonaws.com"
DB_PORT = "5432"
DB_USER = "postgres"
DB_PASSWORD = "biplop123bB#"
DB_NAME = "products_database"

# Create the engine using host configuration
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# SQLAlchemy Base Model
Base = declarative_base()

# Product Model
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)  # Auto-incrementing primary key
    name = Column(String(500), nullable=False)  # Corresponds to "name" in JSON
    image_url = Column(String(500))  # Corresponds to "image_url" in JSON
    master_category = Column(String(100))  # Corresponds to "master_category" in JSON
    product_id = Column(String(100))  # Corresponds to "product_id" in JSON
    price = Column(Numeric(10, 2))  # Corresponds to "price" in JSON
    gender = Column(String(20))  # Corresponds to "gender" in JSON
    article_type = Column(String(100))  # Corresponds to "article_type" in JSON
    season = Column(String(20))  # Corresponds to "season" in JSON
    year = Column(Integer)  # Corresponds to "year" in JSON
    rating = Column(Numeric(3, 2))  # Corresponds to "rating" in JSON
    category = Column(String(100))  # Corresponds to "master_category" in JSON


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
