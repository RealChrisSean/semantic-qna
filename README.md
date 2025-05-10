# Semantic Q&A CLI
A simple command-line FAQ assistant that uses TiDB Cloud’s vector database and AWS Bedrock embeddings to retrieve answers by meaning, not keywords.
---
## 🚀 Features
- **Vector-powered search**  
  Stores question embeddings in TiDB Cloud’s vector column for lightning-fast semantic lookup.  
- **Raw AWS Bedrock calls**  
  No LangChain or wrappers—see exactly how Titan-V2 embeddings are created and consumed.  
- **Zero infra overhead**  
  All you need is a TiDB Serverless cluster and AWS Bedrock credentials.  
- **Pure Python CLI**  
  Interactive shell for asking questions and getting the closest matching answer.
---
## 🛠️ Prerequisites
- **macOS** with **Python 3.8+**  
- AWS CLI v2 configured with a user that can call Bedrock:  
  ```bash
  aws configure