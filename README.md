# Semantic FAQ CLI

Think of this as your go-to command-line buddy that fetches answers based on what you *mean*—not just the exact words you type. Under the hood, it taps into TiDB Cloud’s vector columns and AWS Bedrock Titan-V2 embeddings, all wrapped up in pure Python.

---

## 🚀 Features

- **Semantic search, minus the fluff**  
  Store question embeddings in TiDB and let vector lookups do the heavy lifting.

- **Raw Bedrock power**  
  No LangChain wrappers—just straight JSON calls so you see exactly what Titan-V2 returns.

- **Serverless-ready**  
  A free TiDB Serverless cluster and AWS keys are all you need to get started.

- **Pure Python CLI**  
  Fire it up, ask a question, get an answer—no extra services required.

---

## 🛠️ Prerequisites

- **macOS** with **Python 3.8+**  
- AWS CLI v2 configured (`aws configure`)  
- A TiDB Cloud Serverless cluster (free tier works)  
- Root CA at `/etc/ssl/cert.pem` (macOS default)

---

## 🌐 Web Interface

Prefer a web page over a terminal? Here’s how:

1. **Install FastAPI & Uvicorn**  
   ```bash
   pip install fastapi uvicorn
   ```

2. **Check that `server.py` and `index.html` live in your project folder.**

3. **Run the server**  
   ```bash
   uvicorn server:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Open your browser** to <http://localhost:8000> and start asking questions.