from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pinecone import Pinecone
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance
from tqdm import tqdm
import logging

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QdrantToPineconeMigrateRequest(BaseModel):
    qdrant_api_key: str
    qdrant_url: str
    qdrant_collection: str
    pinecone_api_key: str
    pinecone_db: str
    namespace: str = None
    batch_size: int = 100  # default batch size

@app.post("/qdrant_to_pinecone")
async def qdrant_to_pinecone(req: QdrantToPineconeMigrateRequest):
    try:
        # Init Qdrant
        qdrant_client = QdrantClient(
            url=req.qdrant_url,
            api_key=req.qdrant_api_key,
            prefer_grpc=True,
            timeout=60.0
        )

        # Get vectors from Qdrant
        scroll_results, _ = qdrant_client.scroll(
            collection_name=req.qdrant_collection,
            scroll_filter=None,
            limit=10000,
            with_payload=True,
            with_vectors=True
        )

        if not scroll_results:
            raise Exception("No data found in Qdrant collection.")

        # Organize data
        ids, vectors, metadatas = [], [], []
        for point in scroll_results:
            ids.append(str(point.id))
            vectors.append(point.vector)
            metadatas.append(point.payload or {})

        vector_dimension = len(vectors[0])  # Assumes all have same dim
        logger.info(f"Fetched {len(ids)} vectors of dim {vector_dimension} from Qdrant")

        # Init Pinecone
        pc = Pinecone(api_key=req.pinecone_api_key)
        pinecone_index = pc.Index(req.pinecone_db)

        # Batch upsert
        batch_size = min(req.batch_size, 500)
        success_count = 0
        for i in tqdm(range(0, len(ids), batch_size), desc="Uploading to Pinecone"):
            batch_ids = ids[i:i + batch_size]
            batch_vectors = vectors[i:i + batch_size]
            batch_metadatas = metadatas[i:i + batch_size]

            pinecone_index.upsert(vectors=[
                {
                    "id": id_,
                    "values": vec,
                    "metadata": meta
                } for id_, vec, meta in zip(batch_ids, batch_vectors, batch_metadatas)
            ], namespace=req.namespace)

            success_count += len(batch_ids)

        return {
            "status": "success",
            "migrated_vectors": success_count,
            "vector_dimension": vector_dimension
        }

    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
