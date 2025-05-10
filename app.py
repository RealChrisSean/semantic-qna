"""
app.py – minimal Bedrock-to-TiDB semantic Q&A demo
"""

import os, json
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
# --------------------------------- #

# optional: show which AWS creds boto3 is using
sts = boto3.client("sts", region_name=AWS_REGION)
print("🔑  Using AWS identity:", sts.get_caller_identity()["Arn"])

# ---------- 1.  Bedrock helper ---------- #
def bedrock_embed(text: str) -> List[float]:
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

def ingest_faqs():
    """
    Initialize TiDBVectorClient, create/recreate the table, and seed FAQs.
    Returns the client instance.
    """
    client = TiDBVectorClient(
        table_name          = TABLE_NAME,
        connection_string   = TIDB_CONN_STR,
        vector_dimension    = VECTOR_DIM,
        drop_existing_table = True
    )
    # Single FAQ insert
    qid = "1"
    question = "What is your return policy?"
    answer = "You can return items within 30 days."
    vec = bedrock_embed(question)
    client.insert(
        ids        = [qid],
        texts      = [question],
        embeddings = [vec],
        metadatas  = [{"answer": answer}],
    )
    # Bulk‐load additional FAQs
    bulk = [
        ("2", "How long does shipping take?", "Standard shipping takes 3–5 business days."),
        ("3", "Do you ship internationally?",  "Yes—we ship to over 35 countries."),
        ("4", "How do I track my order?",      "Check the tracking link in your confirmation email."),
    ]
    ids, texts, embs, metas = [], [], [], []
    for fid, q, a in bulk:
        ids.append(fid)
        texts.append(q)
        embs.append(bedrock_embed(q))
        metas.append({"answer": a})
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

def main() -> None:
    # ---------- 2.  TiDB Vector client ---------- #
    client = TiDBVectorClient(
        table_name         = TABLE_NAME,
        connection_string  = TIDB_CONN_STR,
        vector_dimension   = VECTOR_DIM,
        drop_existing_table= True                 # recreate each run
    )

    # ---------- 3.  Ingest one FAQ ---------- #
    qid      = "1"
    question = "What is your return policy?"
    answer   = "You can return items within 30 days."

    vec = bedrock_embed(question)
    client.insert(
        ids        = [qid],
        texts      = [question],
        embeddings = [vec],
        metadatas  = [{"answer": answer}],
    )
    print("✅  Inserted FAQ into TiDB Vector")

    # ─── 3b. Bulk‐load additional FAQs ───────────────────── #
    bulk = [
        ("2", "How long does shipping take?", "Standard shipping takes 3–5 business days."),
        ("3", "Do you ship internationally?",  "Yes—we ship to over 35 countries."),
        ("4", "How do I track my order?",      "Check the tracking link in your confirmation email."),
    ]
    ids, texts, embs, metas = [], [], [], []
    for fid, q, a in bulk:
        ids.append(fid)
        texts.append(q)
        embs.append(bedrock_embed(q))
        metas.append({"answer": a})
    client.insert(
        ids=ids,
        texts=texts,
        embeddings=embs,
        metadatas=metas
    )
    print(f"🚀  Bulk‐loaded {len(bulk)} FAQs")
    # ────────────────────────────────────────────────────── #

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

        # Figure out which attribute holds the stored question text
        if hasattr(best, "document"):
            stored_q = best.document
        elif hasattr(best, "text"):
            stored_q = best.text
        elif hasattr(best, "payload"):
            stored_q = best.payload
        else:
            stored_q = f"<id {best.id}>"

        print("🎯  Closest stored Q:", stored_q)

        answer = ""
        if hasattr(best, "metadata") and best.metadata:
            answer = best.metadata.get("answer", "")
        if not answer:
            answer = "No answer stored."
        print("💡  Answer:", answer)

if __name__ == "__main__":
    main()