import requests

url = "http://127.0.0.1:8000/pinecone_to_qdrant"
payload = {
    "pinecone_api_key": "pcsk_5V13Zf_1drqbRdhkg9y9RKBYf4eLgjHVaMfCd8TXtCWhhAVdrbTJBWmkykTv9sTF1mzeC",
    "qdrant_api_key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.xm0fDBBK6w0KcKDhNk6zsnTnNC3z-lqt13GXaxMbkr8",
    "qdrant_url": "https://a39cabe9-e04e-41bc-bfc8-c35e32b99b11.eu-west-2-0.aws.cloud.qdrant.io:6333",
    "pinecone_db": "qdrant",
    "collection_name": "qdr"
}
response = requests.post(url, json = payload)

if response.ok:
    print("Response:", response.json())
else:
    print("Failed:", response.status_code, response.text)
