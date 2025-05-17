# server.py
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from pydantic import BaseModel
from app import ingest_faqs, query_faq  # import your refactored functions

app = FastAPI()
@app.get("/", include_in_schema=False)
async def read_index():
    index_path = Path(__file__).resolve().parent / "index.html"
    return FileResponse(index_path)
client = None

class QueryReq(BaseModel):
    question: str

@app.on_event("startup")
def startup():
    global client
    client = ingest_faqs()

@app.post("/query")
def ask(req: QueryReq):
    res = query_faq(req.question, client)
    if not res["question"]:
        raise HTTPException(404, "No semantic match found")
    return res

@app.get("/health")
def health():
    return {"status": "ok"}