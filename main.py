from fastapi import FastAPI, Depends, HTTPException,UploadFile, File, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.sql import text
from pydantic import BaseModel
from DbConfig import Product, get_db, SessionLocal  # Reuse from FetchProducts.py
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
    allow_origins=["*"],  # Allow all origins (for testing purposes). Change to specific domain in production.
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

#Pinecone Configureation
PINECONE_API_KEY = "pcsk_2zr51a_QfYBpPKH2sEfuknu2gGLz6FdB4Ks7Y2GG6eWuUQa1Qgto1NzwwZtrvmdyGx8xMg"



#initialize pinecone
try :
        pc = Pinecone(api_key = PINECONE_API_KEY)
        print("Pinecone Initialized")
        image_index = pc.Index(host="https://image-index-ugesh32.svc.aped-4627-b74a.pinecone.io")
        text_index = pc.Index('text-index')
        print("Indexes are ready")

except Exception as e:
        print("Failed to initialize Pinecoone ")    


@app.on_event("startup")
def startup_event():
    """
    Initialize the database connection pool and pinecone when the app starts.
    """

    # Test the database  connection during startup
    with SessionLocal() as db:
        try:
            db.execute(text("SELECT 1"))  # Test the connection
            print("Database connection pool created successfully.")
        except Exception as e:
            print(f"Failed to connect to the database: {e}")


# Products API
@app.get("/products", response_model=list[dict])
def get_products(skip: int = 0, limit: int = 10, random: bool = False, db: Session = Depends(get_db)):
    """
    Fetch products from the database with optional pagination and randomization.
    :param skip: Number of products to skip for pagination.
    :param limit: Number of products to fetch.
    :param random: If True, fetch random products instead of paginated.
    :param db: Database session dependency.
    :return: JSON response with the list of products.
    """
    try:
        if random:
            products = db.query(Product).order_by(func.random()).limit(limit).all()
        else:
            products = db.query(Product).offset(skip).limit(limit).all()

        return [
             {
                "id": product.id if product.id is not None else 0,
                "name": product.name if product.name is not None else "",
                "category_name": product.category_name if product.category_name is not None else "",
                "image_url": product.image_url if product.image_url is not None else "",
                "master_category": product.master_category if product.master_category is not None else "",
                "product_id": product.product_id if product.product_id is not None else "",
                "price": float(product.price) if product.price is not None else 0.0,  # Handle None price
                "gender": product.gender if product.gender is not None else "",
                "sub_category": product.sub_category if product.sub_category is not None else "",
                "article_type": product.article_type if product.article_type is not None else "",
                "season": product.season if product.season is not None else "",
                "year": product.year if product.year is not None else 0,
                "rating": float(product.rating) if product.rating is not None else None,  # Handle None rating
            }
            for product in products
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching products: {str(e)}")


###################################################################
##Image Search Part #############################################
##################################################################

# Temporary folder for saving uploaded images
TEMP_FOLDER = "./tmp"
if not os.path.exists(TEMP_FOLDER):
    os.makedirs(TEMP_FOLDER)


@app.post('/upload_image')
async def search_image(image: UploadFile = File(...), db: Session = Depends(get_db)):
    start_time = time.time()

    try:
        # Save the uploaded image temporarily
        temp_imgpath = os.path.join(TEMP_FOLDER, image.filename)
        with open(temp_imgpath, "wb") as f:
            f.write(await image.read())

        # Extract features from the saved image
        query_features = FeatureExtractor.extract_image_embedding(temp_imgpath)

        #convert to list for pinecone
        query_features = query_features.tolist()

    except Exception as e:
        print(f"Error during image extraction: {e}")
        return JSONResponse(content={"error": "Image extraction failed"}, status_code=500)

    try:
        # Perform similarity search in Pinecone using the image embedding
        results = image_index.query(
            namespace = "image_embedding",
            vector=query_features,
            top_k=20,
            include_metadata=True
        )

    except Exception as e:
        print(f"Error during image search: {e}")
        return JSONResponse(content={"error": "Image search failed"}, status_code=500)

    #Extract the matching product ids
    product_ids = [match['id'] for match in results['matches']]

    #fetch the matching products from db
    detailed_products = fetch_product_details(db, product_ids, results['matches'])
    print(detailed_products)
    if not detailed_products:
            raise HTTPException(status_code=404, detail="No products found in the database")

        # Clean up the temporary image
    if os.path.exists(temp_imgpath):
        os.remove(temp_imgpath)

    end_time = time.time()
    return {"result": detailed_products}











##################################################
##Text Search Part ###############################
##################################################

# Pydantic model for the text search request
class TextQueryRequest(BaseModel):
    query_text: str

# Endpoint to upload text and search for similar products
@app.post('/upload_text')
async def search_text(request: TextQueryRequest, db: Session = Depends(get_db)):
    start_time = time.time()

    query_text = request.query_text

    try:
        # Extract text embedding from the query
        text_embedding = FeatureExtractor.extract_text_embedding(query_text)
    except Exception as e:
        print(f"Error during text extraction: {e}")
        return JSONResponse(content={"error": "Text extraction failed"}, status_code=500)
    text_embedding = text_embedding.tolist()
    try:
        # Perform similarity search in Pinecone using the text embedding
        results = text_index.query(
            vector=text_embedding,
            namespace="text_embedding",
            top_k=20,
            include_metadata=True
        )
    
    except Exception as e:
        print(f"Error during image search: {e}")
        return JSONResponse(content={"error": "Text search failed"}, status_code=500)

    #Extract the matching product ids
    product_ids = [match['id'] for match in results['matches']]

    #fetch the matching products from db
    detailed_products = fetch_product_details(db, product_ids, results['matches'])
    print(detailed_products)
    if not detailed_products:
            raise HTTPException(status_code=404, detail="No products found in the database")

    end_time = time.time()
    return {"result": detailed_products}
