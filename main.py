from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.sql import text
from pydantic import BaseModel
from DbConfig import Product, get_db, SessionLocal
from FetchProductsFromDb import fetch_product_details
import time
import os
from pinecone import Pinecone
import FeatureExtractor

from fastapi.middleware.cors import CORSMiddleware

# FastAPI app initialization
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pinecone Configuration
PINECONE_API_KEY = "pcsk_2zr51a_QfYBpPKH2sEfuknu2gGLz6FdB4Ks7Y2GG6eWuUQa1Qgto1NzwwZtrvmdyGx8xMg"

# Initialize Pinecone
try:
    pc = Pinecone(api_key=PINECONE_API_KEY)
    print("Pinecone Initialized")
    image_index = pc.Index(host="https://image-index-ugesh32.svc.aped-4627-b74a.pinecone.io")
    text_index = pc.Index("text-index")
    print("Indexes are ready")
except Exception as e:
    print(f"Failed to initialize Pinecone: {e}")

@app.on_event("startup")
def startup_event():
    with SessionLocal() as db:
        try:
            db.execute(text("SELECT 1"))
            print("Database connection pool created successfully.")
        except Exception as e:
            print(f"Failed to connect to the database: {e}")

# Products API
@app.get("/products", response_model=list[dict])
def get_products(skip: int = 0, limit: int = 10, random: bool = False, db: Session = Depends(get_db)):
    try:
        if random:
            products = db.query(Product).order_by(func.random()).limit(limit).all()
        else:
            products = db.query(Product).offset(skip).limit(limit).all()

        return [
            {
                "id": product.id or 0,
                "name": product.name or "",
                "category_name": product.category_name or "",
                "image_url": product.image_url or "",
                "master_category": product.master_category or "",
                "product_id": product.product_id or "",
                "price": float(product.price) if product.price is not None else 0.0,
                "gender": product.gender or "",
                "sub_category": product.sub_category or "",
                "article_type": product.article_type or "",
                "season": product.season or "",
                "year": product.year or 0,
                "rating": float(product.rating) if product.rating is not None else None,
            }
            for product in products
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching products: {str(e)}")


# Temporary folder for saving uploaded images
TEMP_FOLDER = "./tmp"
if not os.path.exists(TEMP_FOLDER):
    os.makedirs(TEMP_FOLDER)

# Upload Image API with dynamic top_k and similarity filtering
@app.post("/upload_image")
async def search_image(
    image: UploadFile = File(...), 
    db: Session = Depends(get_db),
    top_k: int = Query(10, ge=1, le=50),  # Allows frontend to set top_k (default 10, max 50)
    similarity_threshold: float = Query(0.8, ge=0.0, le=1.0)  # Minimum similarity score (default 0.8)
):
    start_time = time.time()

    try:
        temp_imgpath = os.path.join(TEMP_FOLDER, image.filename)
        with open(temp_imgpath, "wb") as f:
            f.write(await image.read())

        query_features = FeatureExtractor.extract_image_embedding(temp_imgpath).tolist()
    except Exception as e:
        print(f"Error during image extraction: {e}")
        return JSONResponse(content={"error": "Image extraction failed"}, status_code=500)

    try:
        results = image_index.query(
            namespace="image_embedding",
            vector=query_features,
            top_k=top_k,
            include_metadata=True
        )
    except Exception as e:
        print(f"Error during image search: {e}")
        return JSONResponse(content={"error": "Image search failed"}, status_code=500)

    # Apply similarity threshold filtering
    filtered_matches = [match for match in results["matches"] if match["score"] >= similarity_threshold]

    product_ids = [match["id"] for match in filtered_matches]
    detailed_products = fetch_product_details(db, product_ids, filtered_matches)

    if not detailed_products:
        raise HTTPException(status_code=404, detail="No products found with sufficient similarity")

    if os.path.exists(temp_imgpath):
        os.remove(temp_imgpath)

    return {"result": detailed_products}


# Text Query Request Model
class TextQueryRequest(BaseModel):
    query_text: str

# Upload Text API with dynamic top_k and similarity filtering
@app.post("/upload_text")
async def search_text(
    request: TextQueryRequest, 
    db: Session = Depends(get_db),
    top_k: int = Query(10, ge=1, le=50),  # Allows frontend to set top_k
    similarity_threshold: float = Query(0.8, ge=0.0, le=1.0)  # Minimum similarity score
):
    start_time = time.time()

    query_text = request.query_text

    try:
        text_embedding = FeatureExtractor.extract_text_embedding(query_text).tolist()
    except Exception as e:
        print(f"Error during text extraction: {e}")
        return JSONResponse(content={"error": "Text extraction failed"}, status_code=500)

    try:
        results = text_index.query(
            vector=text_embedding,
            namespace="text_embedding",
            top_k=top_k,
            include_metadata=True
        )
    except Exception as e:
        print(f"Error during text search: {e}")
        return JSONResponse(content={"error": "Text search failed"}, status_code=500)

    # Apply similarity threshold filtering
    filtered_matches = [match for match in results["matches"] if match["score"] >= similarity_threshold]

    product_ids = [match["id"] for match in filtered_matches]
    detailed_products = fetch_product_details(db, product_ids, filtered_matches)

    if not detailed_products:
        raise HTTPException(status_code=404, detail="No products found with sufficient similarity")

    return {"result": detailed_products}
