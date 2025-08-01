from fastapi import FastAPI
from pinecone import Pinecone
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from tqdm import tqdm
import numpy as np
from pydantic import BaseModel
import logging

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PineconToQdratMigrateRequest(BaseModel):
    pinecone_api_key: str
    qdrant_api_key: str
    qdrant_url: str
    pinecone_db: str
    collection_name: str
    namespace: str = None  # Optional Pinecone namespace
    batch_size: int = 100  # Default batch size

class PineconetoChromaMigrateRequest(BaseModel):
    pinecone_api_key:str
    chroma_cloud_api:str
    pinecone_db:str
    chroma_db:str
    
    
@app.post('/pinecone_to_qdrant')
async def migrate(req: PineconToQdratMigrateRequest):
    try:
        # Initialize Pinecone
        pc = Pinecone(api_key=req.pinecone_api_key)
        index = pc.Index(req.pinecone_db)
        
        # Initialize Qdrant with longer timeout
        qdrant_client = QdrantClient(
            url=req.qdrant_url,
            api_key=req.qdrant_api_key,
            prefer_grpc=True,
            timeout=60.0  # Increased timeout to 60 seconds
        )

        # Get index stats
        stats = index.describe_index_stats()
        vector_dimension = stats['dimension']
        distance = stats['metric']
        
        # Create collection if it doesn't exist
        if not qdrant_client.collection_exists(req.collection_name):
            qdrant_client.create_collection(
                collection_name=req.collection_name,
                vectors_config=VectorParams(
                    size=vector_dimension,
                    distance=map_pinecone_to_qdrant_distance(distance)
            )
                )

        # Fetch all vector IDs
        all_ids = []
        for page in index.list(limit=100, namespace=req.namespace):
            all_ids.extend(page)
        logger.info(f"Found {len(all_ids)} vector IDs to migrate")

        # Process in batches
        success_count = 0
        batch_size = min(req.batch_size, 500)  # Cap at 500 for safety
        
        for i in tqdm(range(0, len(all_ids), batch_size), desc="Migrating vectors"):
            batch_ids = all_ids[i:i + batch_size]
            
            # Fetch vectors from Pinecone
            pinecone_vectors = index.fetch(ids=batch_ids, namespace=req.namespace).vectors
            
            # Prepare Qdrant points
            points = [
                PointStruct(
                    id=vid,
                    vector=vector.values,
                    payload=vector.metadata or {}
                )
                for vid, vector in pinecone_vectors.items()
                if len(vector.values) == vector_dimension
            ]
            
            # Upsert to Qdrant
            if points:
                qdrant_client.upsert(
                    collection_name=req.collection_name,
                    points=points,
                    wait=True  # Wait for confirmation
                )
                success_count += len(points)

        # Verify migration
        collection_info = qdrant_client.get_collection(req.collection_name)
        
        return {
            "status": "success",
            "migrated_vectors": success_count,
            "collection_count": collection_info.points_count,
            "vector_dimension": vector_dimension,
            "distance_metric": distance
        }

    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

def map_pinecone_to_qdrant_distance(metric: str) -> Distance:
    metric = metric.lower()
    if metric == "cosine":
        return Distance.COSINE
    elif metric == "euclidean":
        return Distance.EUCLID
    elif metric == "dotproduct":
        return Distance.DOT
    else:
        raise ValueError(f"Unsupported Pinecone metric: {metric}")
    
@app.post('/pinecone_to_chroma')
async def pinecone_to_chroma(req:PineconetoChromaMigrateRequest):
    try:
        pc = Pinecone(api_key=pinecone_api_key)
        index = pc.Index(pinecone_db)  # your existing index

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

