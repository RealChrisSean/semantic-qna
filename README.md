# Semantic FAQ CLI

Think of this as your go-to command-line buddy that fetches answers based on what you *mean*—not just the exact words you type. Under the hood, it taps into [TiDB Cloud’s](https://auth.tidbcloud.com/login) vector columns and [AWS Bedrock Titan-V2 embeddings](https://docs.aws.amazon.com/bedrock/latest/userguide/titan-embedding-models.html), all wrapped up in pure Python.

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

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Required Environment Variables

Create a `.env` file based on the provided template and fill in your own values:

```bash
cp .env.example .env
# edit .env with your secrets
```

- `DATABASE_URL` – TiDB connection string
- `AWS_REGION` – AWS region for Bedrock (defaults to `us-east-1`)
- `FAQ_FILE` – path to the FAQ JSON file (defaults to faqs.json)
---

## 🌐 Web Interface

Prefer a web page over a terminal? Here’s how:

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Check that `server.py` and `index.html` live in your project folder.**

3. **Start the dev server with a progress bar**
   ```bash
   python run_with_bar.py
   ```

   *(This script runs Uvicorn and waits for the `/health` endpoint to respond before handing over the logs.)*
4. **Run the server manually (alternative)**
   ```bash
   uvicorn server:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Open your browser** to <http://localhost:8000> and start asking questions.

6. The included `index.html` uses React (loaded via CDN) so you get a modern UI
   with a dark/light toggle and a growing history of your queries and results.


## Running Tests

Install development dependencies and run pytest:

```bash
pip install -r requirements.txt
pytest
```
