from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from qdrant_client import QdrantClient
from chromadb import Client as ChromaClient
from chromadb.config import Settings
import logging

app = FastAPI()
logger = logging.getLogger("migration")
logging.basicConfig(level=logging.INFO)

class QdrantToChromaMigrationRequest(BaseModel):
    qdrant_url: str
    qdrant_api_key: str
    qdrant_collection: str
    chroma_api_key: str
    chroma_tenant: str
    chroma_collection: str

@app.post("/migrate/qdrant-to-chroma")
def migrate_qdrant_to_chroma(req: QdrantToChromaMigrationRequest):
    try:
        # Connect to Qdrant
        qdrant_client = QdrantClient(
            url=req.qdrant_url,
            api_key=req.qdrant_api_key
        )

        # Fetch all vectors, payloads, and ids from Qdrant
        scroll_results = qdrant_client.scroll(
            collection_name=req.qdrant_collection,
            scroll_filter=None,
            limit=10000,
            with_payload=True,
            with_vectors=True
        )

        if not scroll_results[0]:
            raise Exception("No data found in Qdrant collection.")

        vectors = []
        metadatas = []
        documents = []
        ids = []

        for point in scroll_results[0]:
            vectors.append(point.vector)
            metadatas.append(point.payload if point.payload else {})
            documents.append(point.payload.get("document", ""))  # Assumes doc is under 'document'
            ids.append(str(point.id))

        # Connect to Chroma Cloud
        chroma_client = ChromaClient(Settings(
            chroma_api_impl="rest",
            chroma_server_host="api.chroma.cloud",
            chroma_server_http_port="443",
            tenant=req.chroma_tenant,
            database="default",
            api_key=req.chroma_api_key,
            anonymized_telemetry=False
        ))

        # Get or create Chroma collection
        collection = chroma_client.get_or_create_collection(name=req.chroma_collection)

        # Push data to Chroma
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=vectors
        )

        return {"status": "success", "message": f"Migrated {len(ids)} vectors from Qdrant to Chroma."}

    except Exception as e:
        logger.exception("Migration failed.")
        return {"status": "error", "message": str(e)}