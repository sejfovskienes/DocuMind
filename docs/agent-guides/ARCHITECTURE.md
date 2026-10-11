# Architecture guide

Updated from source on 2026-10-11 after the consistency refactor.

## Application boundaries

- [app/main.py](../../app/main.py) builds the FastAPI app. Its lifespan initializes SQL tables explicitly; importing the app does not connect to SQL or Qdrant or load inference models.
- [app/database_extension.py](../../app/database_extension.py) owns the declarative base, lazy engine creation, and session factories. Request dependencies close their sessions; worker polling closes each session before sleeping.
- Routes handle HTTP and authentication in app/routes. Schemas in app/schemas use Pydantic v2 configuration. ORM models remain in app/models; persistence helpers remain in app/services.
- [app/base/config](../../app/base/config) exports AuthConfig, DatabaseConfig, DocumentConfig, ModelConfig, VectorDatabaseConfig, WorkerConfig, and EnvironmentConfig from domain_name_config.py modules. Settings are typed class attributes; EnvironmentConfig loads dotenv once with the existing override behavior. Do not print environment values.
- [app/base/extensions](../../app/base/extensions) holds document text/storage helpers, worker polling, and vector result ordering.
- [app/ml](../../app/ml) owns lazy, injectable SentenceTransformer, Transformers NER, and optional ONNX adapters. SQL models and inference models have separate packages.
- [app/worker_launcher.py](../../app/worker_launcher.py) launches the three processor modules using the active interpreter. Processor imports do not start worker loops.

## Document and NLP flow

1. Upload streams the file to storage and creates the document and processing task in one SQL transaction. Failure rolls back both rows and removes the new file.
2. DocumentWorker extracts PDF text, normalizes it, splits overlapping word chunks, obtains embeddings, persists chunks, and uploads vectors.
3. Qdrant uses stable persisted chunk IDs and the configured embedding dimension (768 for all-mpnet-base-v2). Upload failures propagate. Matching SQL chunks are reused after a failed vector upload, so retry does not append duplicates or re-embed. Mismatched stored chunks fail clearly.
4. Source files are removed only after successful processing. Failed work keeps its source file.
5. NER reads ordered SQL chunks and stores structured entity results. Legacy string entity values remain readable by the chunk schema.
6. Summarization has no summary-generation/persistence implementation. Its processor raises explicitly and the task becomes FAILED without printing document text.

Routes verify document ownership before retrieval/deletion, metadata access, or NLP task creation. Task lookup checks both document ownership and any user ID supplied by the stored task payload.

## Compatibility and remaining limits

SQL column names, task enum values, route URLs/methods, and response keys remain compatibility surfaces. The stored/schema spelling finshed_at is retained. The unused metadata_id chunk schema field is optional for compatibility. Qdrant writes chunk_id and the legacy chunkk_id payload key.

No database migrations, lease recovery, or distributed transaction system was introduced. SQL and Qdrant writes remain separate operations. Existing malformed/duplicate SQL chunks or legacy vector IDs are not migrated automatically. Deletion still follows the existing SQL workflow; external vector/file retention needs a separate policy. Text normalization retains the existing ASCII-only behavior, and chunk size counts whitespace-separated words rather than model tokens.
