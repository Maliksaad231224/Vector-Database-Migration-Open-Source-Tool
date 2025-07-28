# Import the Pinecone library
from pinecone import Pinecone
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec 
from pinecone import ServerlessSpec
from langchain_pinecone import PineconeVectorStore

load_dotenv()
import os
# Access environment variables as if they came from the actual environment
PINECONE_API = os.getenv('PINECONE')


# Initialize a Pinecone client with your API key
pc = Pinecone(api_key=PINECONE_API)
index = pc.Index("db")  # your existing index

all_ids = []
for page in index.list(limit=100, namespace=None):  # adjust namespace as needed
    all_ids.extend(page)
print(f"Found {len(all_ids)} vector IDs.")
def fetch_vectors(index, ids, batch_size=100):
    all_vectors = []
    for i in range(0, len(ids), batch_size):
        batch_ids = ids[i:i + batch_size]
        response = index.fetch(ids=batch_ids)

        for vid, vector in response.vectors.items():
            all_vectors.append({
                "id": vid,
                "vector": vector.values,
                "metadata": vector.metadata or {}
            })
    return all_vectors

vectors = fetch_vectors(index, all_ids)

import chromadb
chroma_client = chromadb.Client()

collection = chroma_client.create_collection(name="col")
ids = [vec["id"] for vec in vectors]
print('ids')
embeddings = [vec["vector"] for vec in vectors]
print('embeddigns')
metadatas = [vec.get("metadata", {}) for vec in vectors]
print('metadata')

try:
    collection.add(
        ids=ids,
        embeddings=embeddings,
        metadatas=metadatas
    )
    print('added')
except Exception as e:
    print("Error during collection.add():", str(e))
