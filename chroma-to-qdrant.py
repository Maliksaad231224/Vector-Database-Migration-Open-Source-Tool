from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from chromadb import Client as ChromaClient
from chromadb.config import Settings

app = FastAPI()
logger = logging.getLogger("migration")
logging.basicConfig(level=logging.INFO)

class ChromaToQdrantMigrationRequest(BaseModel):
    chroma_api_key: str
    chroma_tenant: str
    chroma_database: str
    chroma_collection: str

    qdrant_url: str
    qdrant_api_key: str
    qdrant_collection: str

@app.post("/migrate/chroma-to-qdrant")
def migrate_chroma_to_qdrant(req: ChromaToQdrantMigrationRequest):
    try:
        # Initialize Chroma client
        chroma_client = ChromaClient(
            Settings(
                chroma_api_impl="rest",
                chroma_server_host="api.chroma.cloud",
                chroma_server_http_port="443",
                chroma_server_ssl_enabled=True,
                tenant=req.chroma_tenant,
                database=req.chroma_database,
                anonymized_telemetry=False,
                chroma_api_key=req.chroma_api_key
            )
        )

        # Fetch collection data
        chroma_collection = chroma_client.get_collection(name=req.chroma_collection)
        chroma_data = chroma_collection.get(include=["embeddings", "metadatas", "documents"])

        if not chroma_data["ids"]:
            raise HTTPException(status_code=404, detail="No data found in Chroma collection.")

        logger.info(f"Fetched {len(chroma_data['ids'])} records from Chroma")

        # Initialize Qdrant client
        qdrant = QdrantClient(url=req.qdrant_url, api_key=req.qdrant_api_key)

        # Create Qdrant collection
        qdrant.recreate_collection(
            collection_name=req.qdrant_collection,
            vectors_config=VectorParams(size=len(chroma_data["embeddings"][0]), distance=Distance.COSINE),
        )

        # Upload to Qdrant
        qdrant.upload_collection(
            collection_name=req.qdrant_collection,
            ids=chroma_data["ids"],
            vectors=chroma_data["embeddings"],
            payload=chroma_data["metadatas"]
        )

        return {"status": "success", "message": f"{len(chroma_data['ids'])} vectors migrated to Qdrant."}

    except Exception as e:
        logger.exception("Migration failed.")
        return {"status": "error", "message": str(e)}
