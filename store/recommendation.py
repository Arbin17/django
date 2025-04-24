from fastapi import FastAPI, HTTPException, Request
import torch
from transformers import BertTokenizer, BertModel
from sklearn.metrics.pairwise import cosine_similarity
import json
import numpy as np

# Initialize FastAPI app
app = FastAPI(title="Product Recommendation API")

# Load the pre-trained BERT model and tokenizer
tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
model = BertModel.from_pretrained("bert-base-uncased")

# Load products data 
with open(r"c:\Users\Arbin\Downloads\Django\ecoms\ecom\list.json", "r") as f:
    products = json.load(f)

# Function to extract the [CLS] token's embedding
def get_cls_embedding(text):
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
    with torch.no_grad():
        outputs = model(**inputs)
    # Extract the [CLS] token's embedding (first token)
    cls_embedding = outputs.last_hidden_state[:, 0, :]        
    return cls_embedding

# Generate embeddings for all products and store them
product_embeddings = {}
for category, items in products.items():
    for item in items:
        description = item["description"]
        # Get the embedding for the product description
        embedding = get_cls_embedding(description)
        # Store the embedding with the product name as key 
        product_embeddings[item["name"]] = embedding.detach().numpy()

# Function to find the most similar product
def get_recommendations(query, top_n=5):
    query_embedding = get_cls_embedding(query).detach().numpy()
    similarities = {}

    for product_name, product_embedding in product_embeddings.items():
        # Compute cosine similarity between query and product embeddings
        similarity = cosine_similarity(query_embedding, product_embedding.reshape(1, -1))
        similarities[product_name] = similarity[0][0]

    # Sort products based on similarity score (descending)
    sorted_similarities = sorted(similarities.items(), key=lambda x: x[1], reverse=True)

    # Return the top N similar products
    recommendations = []
    for i in range(min(top_n, len(sorted_similarities))):
        product_name = sorted_similarities[i][0]
        for category, items in products.items():
            for item in items:
                if item["name"] == product_name:
                    recommendations.append({
                        "name": product_name,
                        "description": item["description"],
                        "similarity_score": float(sorted_similarities[i][1])
                        # "price": item["price"] if "price" in item else None
                    })
                    break
    return recommendations

# Route to handle product recommendation requests
@app.post("/recommend")
async def recommend(request: Request):
    try:
        data = await request.json()
        if not data or "query" not in data:
            raise HTTPException(status_code=400, detail="Missing query in request")
        
        query = data["query"]
        top_n = data.get("top_n", 5)
        
        recommendations = get_recommendations(query, top_n)
        return {"recommendations": recommendations}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Run the FastAPI app