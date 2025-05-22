"""FastAPI server exposing a simple FAQ query API."""
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from pydantic import BaseModel
from app import ingest_faqs, query_faq  # import your refactored functions
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the TiDB client on startup and yield it for API handlers."""
    global client
    client = ingest_faqs()
    yield
    # (Optional) Place any shutdown logic here

app = FastAPI(lifespan=lifespan)

@app.get("/", include_in_schema=False)
async def read_index():
    """Serve the index page via **GET /** and return the HTML response."""
    index_path = Path(__file__).resolve().parent / "index.html"
    return FileResponse(index_path)
client = None

class QueryReq(BaseModel):
    """Request payload for the ``/query`` endpoint."""
    question: str

@app.post("/query")
def ask(req: QueryReq):
    """POST /query to return the best FAQ answer or a 404 if none match."""
    res = query_faq(req.question, client)
    if not res["question"]:
        raise HTTPException(404, "No semantic match found")
    return res

@app.get("/health")
def health():
    """Simple **GET /health** endpoint returning a status message."""
    return {"status": "ok"}