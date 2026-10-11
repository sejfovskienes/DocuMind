# Architecture Guide

## Scope and evidence

This guide describes the repository state observed in the Python source files cited below. It does not infer behavior from model binaries, environment values, uploads, or runtime execution. Recommendations are labeled separately from observed behavior.

## Application entry points

- The FastAPI application is defined in [app/main.py](../../app/main.py). It creates the app, adds a root route, mounts auth, document, document metadata, and NLP routers, and calls SQLAlchemy Base.metadata.create_all(bind=engine) at module import time.
- Worker process entry modules are app/workers/document_worker/document_worker_processor.py, app/workers/ner_worker/ner_worker_processor.py, and app/workers/summarization_worker/summarization_worker_processor.py. The NER processor uses the literal condition if "__name__==__main__" (including quotes), which is a nonempty string and runs main when the module is imported.
- app/start_all_workers.py defines main() twice and has a main guard after each definition. Its top-level import of the NER processor can enter the NER loop before either guard is reached. If execution reaches the first guard when run as a script, it invokes the first main before the second definition is evaluated; that main calls worker loops sequentially and can block. The later main is written as a terminal launcher, but is not a reliable description of the current runtime path. Its commands target worker packages that have no __main__.py in the reviewed tree.

## Request and persistence flow

1. app/database.py loads environment configuration, constructs a SQLAlchemy engine and SessionLocal, and exposes get_database_session() for request-scoped sessions (closed in finally) plus get_session() for direct callers.
2. app/routes/auth.py exposes registration and login under /auth; app/services/user_service.py hashes passwords and persists users. The bearer-token dependency decodes JWT subject as email, then looks up the user.
3. app/routes/document.py exposes upload, retrieval, and deletion under /documents. Upload writes received bytes to UPLOAD_DIR, creates a Document row through document_service, then saves a queued WorkerTask for document processing through task_service.
4. app/routes/nlp.py queues entity extraction and summarization task rows. app/routes/document_metadata.py queries metadata by document ID.
5. app/services/task_service.py is the shared persistence layer for task rows. Workers find the first queued task matching their task type, then update status and task data through this service.

The SQLAlchemy models in app/models/ define users, documents, chunks, document metadata, and worker tasks. A user has documents; a document has chunks and a one-to-one metadata relationship configured with delete-orphan cascade. Chunk records hold text, token count, embeddings, entities, and topic keywords. Metadata records hold summaries and document-level entity/topic JSON fields. Worker tasks store a JSON payload, task type, status, and timestamps.

## Background processing and vector data

- DocumentWorker (app/workers/document_worker/document_worker.py) polls document-processing tasks. It extracts PDF text with PyMuPDF, cleans it, splits it into overlapping word chunks, generates embeddings using SentenceTransformer, persists DocumentChunk rows, then writes vectors to Qdrant. The Qdrant payload includes user/document/chunk identifiers, chunk index, and text.
- NERWorker (app/workers/ner_worker/ner_worker.py) polls entity-extraction tasks, loads document chunks using document_chunk_service, runs entity extraction per chunk, and writes ner_entities back to SQL.
- SummarizationWorker (app/workers/summarization_worker/summarization_worker.py) polls summarization tasks and retrieves document chunk text from Qdrant. Its current process_summarization_task prints fetched text and has no explicit return value or summary persistence.
- Qdrant integration is centralized in app/vector_database/qdrant_client.py. It creates the configured collection if missing, adds payload indexes, upserts vectors, and scrolls points filtered by user and document. The code declares VECTOR_SIZE = 100 but creates the collection with vector size 768.

## Ownership and change boundaries

- HTTP routing, request dependencies, and response shaping: app/routes/.
- SQLAlchemy tables and relationships: app/models/; request/response shapes: app/schemas/.
- Database configuration/session creation: app/database.py; password hashing and token encode/decode: app/auth.py.
- Domain persistence helpers: app/services/.
- Queue consumers and document/NLP work: app/workers/; task types/statuses: app/core/enum/.
- Vector persistence and retrieval: app/vector_database/qdrant_client.py.

When changing a flow, trace its route, service, model, and worker together. Keep database session ownership explicit: request handlers receive dependency-managed sessions; long-running workers obtain sessions directly.

## Observed gaps and mismatches

These are source-level observations, not runtime conclusions:

- app/routes/document.py returns database objects directly from upload/retrieval routes without a declared response schema, and its retrieval/deletion query by ID after authentication without a visible ownership predicate. The Qdrant retrieval path filters both user and document.
- The ORM DocumentMetadata fields are global_entities and global_topics; app/services/document_metadata_service.py:get_named_entities refers instead to entities and clean_text.
- The worker task model spells its completion field finshed_at; schemas and worker updates repeat this spelling.
- Document worker upload_embeddings uses a boolean-returning Qdrant method but does not check its return value before returning success. In its loop, the finally block marks tasks FINISHED even after the exception path marks them FAILED.
- Qdrant declares VECTOR_SIZE as 100 while collection creation uses 768. The document worker uses all-mpnet-base-v2; verify embedding dimensionality against collection configuration when changing embedding models.
- DocumentWorker.delete_document_from_local_storage removes the uploaded source after processing and clears the SQL file path. This behavior is explicit in the worker source.
- app/workers/ner_worker/ner_worker.py has both ONNX inference helpers and a Transformers pipeline; ner_processing calls the Transformers pipeline helper. Its task loop finally marks the task FINISHED after the exception path can mark it FAILED.

## Recommendations for future changes

- Preserve the route → service → model layering where it fits, and keep vector-specific operations behind the Qdrant client.
- Before changing an entity or task field, search every route, schema, service, model, and worker reference so SQL data and API responses stay aligned.
- For changes to document processing, follow the persisted document ID from upload through task payload, chunk rows, vector payload, and retrieval filters.
