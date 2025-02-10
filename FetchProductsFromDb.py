from sqlalchemy.orm import Session
from typing import List
from fastapi import HTTPException
from DbConfig import Product

def fetch_product_details(db: Session, product_ids: List[str], products: List[dict]):
    try:
        db_products = db.query(Product).filter(Product.product_id.in_(product_ids)).all()

        if not db_products:
            return None  # No products found

        # ✅ Create a dictionary mapping product_id -> DB Product
        product_map = {db_product.product_id: db_product for db_product in db_products}

        # ✅ Preserve similarity order by looking up products in the same order as Pinecone results
        detailed_products = []
        for product in products:
            product_id = product["id"]
            similarity_score = product["score"]

            if product_id in product_map:
                db_product = product_map[product_id]

                detailed_product = {
                    "id": db_product.id,
                    "name": db_product.name,
                    "image_url": db_product.image_url,
                    "master_category": db_product.master_category,
                    "product_id": db_product.product_id,
                    "price": str(db_product.price),
                    "gender": db_product.gender,
                    "article_type": db_product.article_type,
                    "season": db_product.season,
                    "year": db_product.year,
                    "rating": str(db_product.rating),
                    "category": db_product.category,
                    "similarity_score": round(similarity_score, 4),  # ✅ Pass similarity score in response
                }

                detailed_products.append(detailed_product)
            else:
                print(f"⚠️ Warning: Product ID {product_id} not found in database.")

        return detailed_products

    except Exception as e:
        print(f"Error fetching product details: {e}")
        raise HTTPException(status_code=500, detail="Error fetching product details")
