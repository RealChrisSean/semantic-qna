import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fastapi.testclient import TestClient
from unittest.mock import patch
import server


def _create_client():
    """Utility to create TestClient while patching startup."""
    return TestClient(server.app)


def test_health():
    with patch("server.ingest_faqs", return_value="dummy_client"):
        with _create_client() as client:
            res = client.get("/health")
            assert res.status_code == 200
            assert res.json() == {"status": "ok"}


def test_query_endpoint():
    with patch("server.ingest_faqs", return_value="dummy_client"):
        with patch("server.query_faq", return_value={"question": "stored q", "answer": "stored a"}) as mock_query:
            with _create_client() as client:
                res = client.post("/query", json={"question": "user q"})
                assert res.status_code == 200
                assert res.json() == {"question": "stored q", "answer": "stored a"}
                mock_query.assert_called_with("user q", "dummy_client")
