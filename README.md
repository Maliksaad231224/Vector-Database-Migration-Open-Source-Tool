# 🧠 Vector Database Migration Tool

A lightweight and flexible utility to **migrate vector embeddings and metadata** between popular vector databases such as **Pinecone**, **ChromaDB**, **Weaviate**, **Qdrant**, and more.

> ⚙️ Built for developers, data scientists, and ML engineers working with embeddings, LLM apps, and retrieval-augmented generation (RAG) pipelines.

---

## 🚀 Features

- 🔄 Migrate vector data between multiple vector database providers
- 📦 Support for embeddings, metadata, and associated documents
- 🔌 Plug-and-play support for common vector DBs (e.g., Pinecone, ChromaDB)
- 📂 Export to and import from intermediate formats (JSON, CSV, or NumPy)
- 🔍 Logging and validation to ensure data integrity
- 🛠️ Easy to customize or extend for your specific pipeline

---

## 📁 Supported Sources & Destinations

| Source DB | Destination DB |
|-----------|----------------|
| Pinecone  | ChromaDB       | 
| ChromaDB  | Pinecone       | 
| Pinecone  | Qdrant         | 
| Qdrant    | Pinecone       | 


## 🧰 Requirements

- Python 3.10+
- `pinecone-client`
- `chromadb`
- `qdrant-client`

Install dependencies:

```bash
pip install -r requirements.txt
