import subprocess
import sys
import unittest
from pathlib import Path


class ImportSafetyTests(unittest.TestCase):
    def test_application_and_processors_do_not_start_services_on_import(self):
        script = """
import sys
from unittest.mock import patch

with patch("dotenv.load_dotenv", return_value=False), \
     patch("sqlalchemy.create_engine") as create_engine, \
     patch("qdrant_client.QdrantClient") as qdrant_client:
    import app.main
    import app.worker_launcher
    import app.workers.document_worker.document_worker_processor
    import app.workers.ner_worker.ner_worker_processor
    import app.workers.summarization_worker.summarization_worker_processor
    create_engine.assert_not_called()
    qdrant_client.assert_not_called()

assert "sentence_transformers" not in sys.modules
assert "transformers" not in sys.modules
assert "onnxruntime" not in sys.modules
assert app.main.app.openapi()["paths"]
"""
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
