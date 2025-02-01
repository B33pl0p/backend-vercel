from sqlalchemy.orm import Session
from typing import List
from fastapi import HTTPException
from DbConfig import Product
def fetch_product_details(db: Session, product_ids: List[str], products: List[dict]):
    try:
        # Query the database for products by their IDs
        db_products = db.query(Product).filter(Product.product_id.in_(product_ids)).all()

        if not db_products:
            return None  # No products found

        # Map the results to a more detailed response
        detailed_products = []
        for db_product, product in zip(db_products, products):
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
                "category":db_product.category,
            }
            detailed_products.append(detailed_product)

        return detailed_products

    except Exception as e:
        print(f"Error fetching product details: {e}")
        raise HTTPException(status_code=500, detail="Error fetching product details")
