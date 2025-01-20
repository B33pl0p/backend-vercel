import time
from FetchProducts import Product, get_db
from fastapi import FastAPI, Depends, Query, Request, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
import FeatureExtractor
import VectorSearch
import base64
import os
from pydantic import BaseModel
from sqlalchemy import func

app = FastAPI()

# CORS configuration with "*" to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Helper function to fetch product details
def fetch_product_details(db, product_ids, products):
    """Fetch product details from the database and format the response."""
    try:
        result_products = db.query(Product).filter(Product.product_id.in_(product_ids)).all()

        if not result_products:
            return None
        
        detailed_products = []
        for product in result_products:
            detailed_products.append({
                    "product_id": product.product_id,
                    "gender": product.gender,
                    "master_category": product.master_category,
                    "sub_category": product.sub_category,
                    "article_type": product.article_type,
                    "base_colour": product.base_colour,
                    "season": product.season,
                    "year": product.year,
                    "product_display_name": product.product_display_name,
                    "price": product.price,
                    "rating": product.rating,
                    "image_data": base64.b64encode(product.image_data).decode('utf-8'),  # Directly base64 encode here
                    "similarity": next(item['similarity'] for item in products if item['product_id'] == product.product_id)
                })
        return detailed_products
    except Exception as e:
        print(f"Error during product fetching: {e}")
        return None

@app.get("/products")
def read_products(
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    #start_time = time.time()

    # Fetch products from the database
    products = db.query(Product).order_by(func.random()).limit((limit)).all()
    # Process products and encode image_data as Base64
    result = []
    for product in products:
        product_dict = product.__dict__.copy()

        # Encode image_data as Base64 if it exists
        if product.image_data:
            product_dict['image_data'] = base64.b64encode(product.image_data).decode("utf-8")
        else:
            product_dict['image_data'] = None
        
        result.append(product_dict)
    
    #end_time = time.time()
    #print(f"Time taken for read_products: {end_time - start_time:.4f} seconds")
    
    return {"result": result}

TEMP_FOLDER = "./tmp"

# Ensure the temporary folder exists
if not os.path.exists(TEMP_FOLDER):
    os.makedirs(TEMP_FOLDER)

@app.post('/upload_image')
async def search_image(image: UploadFile = File(...) , db: Session = Depends(get_db)):
    start_time = time.time()

    # Read and extract features directly from uploaded image
    try:
        temp_imgpath = os.path.join(TEMP_FOLDER, image.filename)
        with open(temp_imgpath, "wb") as f:
            f.write(await image.read())

        # Extract features from the saved image
        feature_start_time = time.time()
        query_features = FeatureExtractor.extract_image_embedding(temp_imgpath)
        feature_end_time = time.time()
        print(f"Time taken for feature extraction: {feature_end_time - feature_start_time:.4f} seconds")

    except Exception as e:
        print(f"Error during extraction: {e}")
        return JSONResponse(content={"error": "Feature extraction failed"}, status_code=500)

    # Search in the vector database for similar images
    try:
        search_start_time = time.time()
        products = VectorSearch.search_by_image_embedding(query_features)
        search_end_time = time.time()
        print(f"Time taken for similarity search: {search_end_time - search_start_time:.4f} seconds")
    
    except Exception as e:
        print(f"Error during searching: {e}")
        return JSONResponse(content={"error": "Vector search failed"}, status_code=500)
    
    product_ids = [product['product_id'] for product in products]

    # Reuse the helper function for fetching and formatting products
    detailed_products = fetch_product_details(db, product_ids, products)
    

    if detailed_products is None:
        return JSONResponse(content={"error": "No products found in the database"}, status_code=404)

    # Clean up the temporary image
    if os.path.exists(temp_imgpath):
        os.remove(temp_imgpath)

    end_time = time.time()
    #print(f"Total time for search_image: {end_time - start_time:.4f} seconds")
    
    return {"result": detailed_products} if detailed_products else JSONResponse(
        content={"error": "No matching results found"}, status_code=404
    )

class TextQueryRequest(BaseModel):
    query_text: str

@app.post('/upload_text')
async def search_text(request: TextQueryRequest, db: Session = Depends(get_db)):
    start_time = time.time()

    query_text = request.query_text  # Extract query_text from the request body
    
    # Extract text embedding
    try:
        feature_start_time = time.time()
        text_embedding = FeatureExtractor.extract_text_embedding(query_text)
        feature_end_time = time.time()
        print(f"Time taken for text feature extraction: {feature_end_time - feature_start_time:.4f} seconds")
    except Exception as e:
        print(f"Error during extraction: {e}")
        return JSONResponse(content={"error": "Text extraction failed"}, status_code=500)

    # Search in the vector database for similar products based on the text embedding
    try:
        search_start_time = time.time()
        products = VectorSearch.search_by_text_embedding(text_embedding)
        search_end_time = time.time()
        print(f"Time taken for vector search: {search_end_time - search_start_time:.4f} seconds")
    
    except Exception as e:
        print(f"Error during searching: {e}")
        return JSONResponse(content={"error": "Vector search failed"}, status_code=500)

    product_ids = [product['product_id'] for product in products]

    # Reuse the helper function for fetching and formatting products
    detailed_products = fetch_product_details(db, product_ids, products)
    
    if detailed_products is None:
        return JSONResponse(content={"error": "No products found in the database"}, status_code=404)

    end_time = time.time()
    print(f"Total time for search_text: {end_time - start_time:.4f} seconds")

    return {"result": detailed_products} if detailed_products else JSONResponse(
        content={"error": "No matching results found"}, status_code=404
    )

#uvicorn main:app --port 4000 --host 0.0.0.0 --reload