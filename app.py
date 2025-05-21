"""
app.py – minimal Bedrock-to-TiDB semantic Q&A demo
"""

import json
import os
from pathlib import Path
from typing import List

import boto3
from dotenv import load_dotenv
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

def get_stored_question_text(result):
    """Extract the stored question text from a query result."""
    if hasattr(result, "document"):
        return result.document
    elif hasattr(result, "text"):
        return result.text
    elif hasattr(result, "payload"):
        return result.payload
    else:
        return f"<id {result.id}>"

def get_answer_from_metadata(result):
    """Extract the answer from the metadata of a query result."""
    if hasattr(result, "metadata") and result.metadata:
        return result.metadata.get("answer", "No answer stored.")
    return "No answer stored."

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
    # Extract stored question and answer
    stored_q = get_stored_question_text(best)
    answer = get_answer_from_metadata(best)
    return {"question": stored_q, "answer": answer}

# ----------------------------------------- #

def main() -> None:
    client = ingest_faqs()
    print(f"🚀  Loaded FAQs from {FAQ_FILE}")

    # ---------- 4.  Interactive loop ---------- #
    while True:
        user_q = input("\n🧐  Ask a question ('exit' to quit): ").strip()
        if user_q.lower() in {"exit", "quit"}:
            break

        q_vec   = bedrock_embed(user_q)
        top_k   = client.query(q_vec, k=3)        # returns list of QueryResult

        if not top_k:
            print("🤷  No match found.")
            continue

        best = top_k[0]
        stored_q = get_stored_question_text(best)
        print("🎯  Closest stored Q:", stored_q)
        
        answer = get_answer_from_metadata(best)
        print("💡  Answer:", answer)

if __name__ == "__main__":
    main()
