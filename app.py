"""
app.py – minimal Bedrock-to-TiDB semantic Q&A demo
"""

import os, json
from pathlib import Path
from dotenv import load_dotenv
import boto3
from typing import List
from tidb_vector.integrations import TiDBVectorClient

# ---------- 0.  Config ---------- #
load_dotenv()                                  # loads .env

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

TIDB_CONN_STR = os.getenv("DATABASE_URL")

VECTOR_DIM = 1024                              # Titan-V2 output size
TABLE_NAME = "faqs"                            # create / recreate each run
FAQ_FILE = os.getenv("FAQ_FILE", "faqs.json")  # FAQ data in JSON format
# --------------------------------- #

# optional: show which AWS creds boto3 is using
sts = boto3.client("sts", region_name=AWS_REGION)
print("🔑  Using AWS identity:", sts.get_caller_identity()["Arn"])

# ---------- 1.  Bedrock helper ---------- #
def bedrock_embed(text: str) -> List[float]:
    """Call AWS Bedrock to generate Titan-2 embeddings and return 1024 floats."""
    brt = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    payload = json.dumps({"inputText": text})
    resp = brt.invoke_model(
        modelId="amazon.titan-embed-text-v2:0",
        contentType="application/json",
        accept="application/json",
        body=payload,
    )
    data = json.loads(resp["body"].read())
    return data["embeddingsByType"]["float"]      # 1024-element list

def ingest_faqs(file_path: str = FAQ_FILE):
    """Create the table and load FAQs from a JSON file."""
    client = TiDBVectorClient(
        table_name          = TABLE_NAME,
        connection_string   = TIDB_CONN_STR,
        vector_dimension    = VECTOR_DIM,
        drop_existing_table = True,
    )

    faq_path = Path(file_path)
    with faq_path.open("r", encoding="utf-8") as f:
        faqs = json.load(f)

    ids, texts, embs, metas = [], [], [], []
    for row in faqs:
        q = row["question"]
        ids.append(row["id"])
        texts.append(q)
        embs.append(bedrock_embed(q))
        metas.append({"answer": row["answer"]})

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

# ----------------------------------------- #

    client = ingest_faqs()
    print(f"🚀  Loaded FAQs from {FAQ_FILE}")

    # ---------- 4.  Interactive loop ---------- #
    while True:
        user_q = input("\n🧐  Ask a question ('exit' to quit): ").strip()
        if user_q.lower() in {"exit", "quit"}:
            break

        res = query_faq(user_q, client)
        if not res["question"]:
            print("🤷  No match found.")
            continue

        print("🎯  Closest stored Q:", res["question"])
        print("💡  Answer:", res["answer"])

if __name__ == "__main__":
    main()