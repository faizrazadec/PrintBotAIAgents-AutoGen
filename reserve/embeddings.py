import json
import os
import chromadb
from langchain_openai import OpenAIEmbeddings

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

embeddings_model = OpenAIEmbeddings(
    model="text-embedding-3-large",
    openai_api_key=OPENAI_API_KEY
    )

with open("products.json", "r", encoding="utf-8") as file:
    data = json.load(file)

json_string = data[0]
products = json.loads(json_string)
products = products[:4]

product_list = []

embeddings_list = []
references = []
for product in products:
    product_string = ""
    for key, value in product.items():
        product_string += f"{key}: {value}\n"
    
    # product_embedding = embeddings_model.embed_documents(product_string)
    # embeddings_list.append(product_embedding)
    references.append(product["reference"])
    product_list.append(product_string)
    print(product_list)

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="product_embeddings")

# collection.add(
#     ids=references,
#     embeddings=embeddings_list,
# )

# print("Embeddings stored in ChromaDB successfully!")

# Function to retrieve similar products based on user query
def retrieve_similar_products(user_query, top_k=2):
    # Step 1: Embed the user query
    query_embedding = embeddings_model.embed_documents([user_query])[0]
    
    # Step 2: Query ChromaDB for similar embeddings
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    
    # Step 3: Retrieve and display the results
    retrieved_ids = results["ids"][0]  # List of IDs (references) of the most similar products
    retrieved_distances = results["distances"][0]  # Corresponding similarity scores
    
    print(f"Top {top_k} similar products to your query:")
    for i, product_id in enumerate(retrieved_ids):
        # Find the corresponding product in the original list
        product_index = references.index(product_id)
        product_info = product_list[product_index]
        similarity_score = retrieved_distances[i]
        
        print(f"\nProduct {i + 1}:")
        print(f"Reference ID: {product_id}")
        print(f"Similarity Score: {similarity_score:.4f}")
        print(f"Details:\n{product_info}")

# Example usage: Get user query and retrieve similar products
if __name__ == "__main__":
    user_query = "Find a product in category: Business Card"
    retrieve_similar_products(user_query, top_k=3)
