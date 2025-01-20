import psycopg2
import numpy as np

# PostgreSQL Connection Details
DB_CONFIG = {
    "dbname": "products_db",
    "user": "postgres",
    #"password": "7878",
    "password" : "biplop123bB#",
    "host": "database-products.c9kqgsu44jjh.eu-north-1.rds.amazonaws.com",
    "port": "5432",
}

def search_by_image_embedding(image_embedding, limit=5):
    """Search in PostgreSQL using image embedding and display cosine similarity."""
    results = _search_in_postgresql(image_embedding, "image_embedding", "image_embedding_idx", limit)
    
    # Display the results with cosine similarity
    for result in results:
        print(f"Product ID: {result['product_id']}, Cosine Similarity: {result['similarity']}")
    
    return results

def search_by_text_embedding(text_embedding, limit=5):
    """Search in PostgreSQL using text embedding and display cosine similarity."""
    results = _search_in_postgresql(text_embedding, "text_embedding", "text_embedding_idx", limit)
    
    # Display the results with cosine similarity
    for result in results:
        print(f"Product ID: {result['product_id']}, Cosine Similarity: {result['similarity']}")
    
    return results
def _search_in_postgresql(query_vector, search_column, index_name, limit):
    """Internal function for searching in PostgreSQL using pgvector."""
    # Connect to PostgreSQL
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()

    # Convert the query vector to a string formatted as a PostgreSQL array
    query_vector_str = "{" + ",".join(map(str, query_vector)) + "}"

    # Vector similarity search query using pgvector
    search_query = f"""
    SET LOCAL enable_indexscan = true;  -- Enable index scan for better performance with indexes.
    SET LOCAL enable_bitmapscan = false;  -- Disable bitmap scan to force usage of index (optional)
    
    SELECT product_id, 
           1 - ({search_column} <=> %s::vector) AS similarity
    FROM products
    WHERE {search_column} IS NOT NULL
    ORDER BY similarity DESC  -- Ensure ordering by highest similarity (DESC)
    LIMIT %s;  -- Limit the number of results returned
    """

    # Execute the query
    cursor.execute(search_query, (query_vector.tolist(), limit))
    rows = cursor.fetchall()

    # Process results: Return only product_id and similarity score
    processed_results = [
        {"product_id": row[0], "similarity": row[1]} for row in rows
    ]

    # Close the connection
    cursor.close()
    connection.close()

    return processed_results
