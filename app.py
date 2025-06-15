"""
app.py – minimal Bedrock-to-TiDB semantic Q&A demo
"""

import os, json
from pathlib import Path
from dotenv import load_dotenv
import boto3
from typing import List
from sqlalchemy import text
from sqlalchemy import create_engine
from tidb_vector.integrations import TiDBVectorClient
import time


# ---------- 0.  Config ---------- #
load_dotenv()                                  # loads .env

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# reuse Bedrock client and cache embeddings
_BEDROCK_CLIENT = boto3.client("bedrock-runtime", region_name=AWS_REGION)
_EMBED_CACHE: dict[str, list[float]] = {}


TIDB_CONN_STR = os.getenv("DATABASE_URL")

VECTOR_DIM = 1024                              # Titan-V2 output size
TABLE_NAME = "faqs"                            # create / recreate each run
FAQ_FILE = os.getenv("FAQ_FILE", "faqs.json")  # FAQ data in JSON format
# --------------------------------- #

# optional: show which AWS creds boto3 is using
sts = boto3.client("sts", region_name=AWS_REGION)
print("🔑  Using AWS identity: <SECRET>")

# ---------- 1.  Bedrock helper ---------- #
def bedrock_embed(text: str) -> List[float]:
    """Call AWS Bedrock to generate Titan-2 embeddings and return 1024 floats."""
    if text in _EMBED_CACHE:
        return _EMBED_CACHE[text]
    payload = json.dumps({"inputText": text})
    resp = _BEDROCK_CLIENT.invoke_model(
        modelId="amazon.titan-embed-text-v2:0",
        contentType="application/json",
        accept="application/json",
        body=payload,
    )
    data = json.loads(resp["body"].read())
    vec = data["embeddingsByType"]["float"]
    _EMBED_CACHE[text] = vec
    return vec

def batch_embed_batch(texts: List[str]) -> List[List[float]]:
    """Embed multiple texts in one Titan batch request."""
    brt = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    resp = brt.invoke_model(
        modelId="amazon.titan-embed-text-v2:0",
        contentType="application/json",
        accept="application/json",
        body=json.dumps({"inputTextArray": texts}),
    )
    data = json.loads(resp["body"].read())
    return data["embeddingsByType"]["floatArray"]

def ingest_faqs(file_path: str = FAQ_FILE):
    """Create the table and load FAQs from a JSON file."""
    client = TiDBVectorClient(
        table_name          = TABLE_NAME,
        connection_string   = TIDB_CONN_STR,
        vector_dimension    = VECTOR_DIM,
        drop_existing_table = False,
    )

    # Check if the table already has data using a standalone engine
    engine = create_engine(TIDB_CONN_STR)
    with engine.connect() as conn:
        row = conn.execute(text(f"SELECT 1 FROM {TABLE_NAME} LIMIT 1")).first()
    if row is not None:
        return client

    faq_path = Path(file_path)
    with faq_path.open("r", encoding="utf-8") as f:
        faqs = json.load(f)

    ids   = [row["id"] for row in faqs]
    texts = [row["question"] for row in faqs]
    metas = [{"answer": row["answer"]} for row in faqs]

    # Batch embed all questions at once
    embs = batch_embed_batch(texts)

    client.insert(ids=ids, texts=texts, embeddings=embs, metadatas=metas)
    return client

def query_faq(question: str, client=None):
    """
    Given a question string, returns a dict with the top stored question and answer.
    """
    if client is None:
        client = TiDBVectorClient(
            table_name         = TABLE_NAME,
            connection_string  = TIDB_CONN_STR,
            vector_dimension   = VECTOR_DIM,
            drop_existing_table=False
        )
    q_vec = bedrock_embed(question)
    results = client.query(q_vec, k=1)
    if not results:
        return {"question": None, "answer": None}
    best = results[0]
    # Determine stored question text
    if hasattr(best, "document"):
        stored_q = best.document
    elif hasattr(best, "text"):
        stored_q = best.text
    elif hasattr(best, "payload"):
        stored_q = best.payload
    else:
        stored_q = f"<id {best.id}>"
    # Extract answer metadata
    answer = (best.metadata or {}).get("answer", "No answer stored.")
    return {"question": stored_q, "answer": answer}

def query_by_vec(q_vec: list[float], client):
    """
    Given an embedding vector, query TiDB and extract the best question/answer.
    """
    results = client.query(q_vec, k=1)
    if not results:
        return {"question": None, "answer": None}
    best = results[0]
    if hasattr(best, "document"):
        stored_q = best.document
    elif hasattr(best, "text"):
        stored_q = best.text
    elif hasattr(best, "payload"):
        stored_q = best.payload
    else:
        stored_q = f"<id {best.id}>"
    answer = (best.metadata or {}).get("answer", "No answer stored.")
    return {"question": stored_q, "answer": answer}

# ----------------------------------------- #

def main():
    client = ingest_faqs()
    print(f"🚀  Loaded FAQs from {FAQ_FILE}")

    # ---------- 4.  Interactive loop ---------- #
    while True:
        user_q = input("\n🧐  Ask a question ('exit' to quit): ").strip()
        if user_q.lower() in {"exit", "quit"}:
            break

        total_start = time.perf_counter()

        # embed timing
        embed_start = time.perf_counter()
        q_vec = bedrock_embed(user_q)
        embed_elapsed = time.perf_counter() - embed_start

        # query timing
        query_start = time.perf_counter()
        res = query_by_vec(q_vec, client)
        query_elapsed = time.perf_counter() - query_start

        total_elapsed = time.perf_counter() - total_start

        if not res["question"]:
            print("🤷  No match found.")
            continue

        print("🎯  Closest stored Q:", res["question"])
        print("💡  Answer:", res["answer"])
        print(f"⏱  Embed time: {embed_elapsed:.4f} seconds")
        print(f"⏱  Query time: {query_elapsed:.4f} seconds")
        print(f"⏱  Total time: {total_elapsed:.4f} seconds")

if __name__ == "__main__":
    main()