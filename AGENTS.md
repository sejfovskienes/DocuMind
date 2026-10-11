# Guidance for agents working on DocuMind

## Start here

At the start of every session in this repository, read and follow [Project context and agent behavior](.agents/project-context.md) before working. This file contains the user's standing behavior and permission rules; it takes precedence over older inferred preferences in the guides.

Read [the guide index](docs/agent-guides/README.md), then the guides relevant to the task. These files were reviewed and updated on 2026-10-11 after the consistency refactor. Recheck the actual implementation before relying on them after later changes.

- [Architecture](docs/agent-guides/ARCHITECTURE.md): module responsibilities, entry points, data flow, and integration boundaries.
- [Code conventions](docs/agent-guides/CODE_CONVENTIONS.md): observed patterns and evidence, with inferred choices labeled.
- [Clean code](docs/agent-guides/CLEAN_CODE.md): recommended rules for new or changed code.
- [Workers and validation](docs/agent-guides/WORKERS_AND_VALIDATION.md): task lifecycle, configuration, known gaps, and verification strategy.

## User preferences established in this session

- Analyze the existing folder and save reusable guidance before implementing the user's later change requests.
- Use smaller-model subagents for analysis subtasks. This review used three gpt-6-luna agents with separate document ownership.
- Add Markdown guidance for clean code.

The user requested the consistency refactor, domain config/extensions, separate inference model classes, package exports, and Ruff formatting. Use unittest for the existing focused regressions. No dependency-manager migration or general replacement architecture has been selected. Keep future changes within their requested scope.

## Repository map

- Python 3.12 is pinned in .python-version; pyproject.toml declares Python >=3.12.
- app/main.py contains the FastAPI application; lifespan startup initializes SQL tables. Root main.py is a greeting script.
- app/routes/ contains HTTP handlers and authentication dependencies.
- app/schemas/ contains Pydantic request/response shapes; app/models/ contains SQLAlchemy persistence models.
- app/services/ contains persistence and application helpers, typically receiving a SQLAlchemy Session.
- app/workers/ contains document, NER, and summarization workers, guarded processor entry modules, and shared task outcome handling.
- app/base/config/ contains typed domain configuration classes in {domain_name}_config.py files; app/base/extensions/ contains shared helpers; app/ml/ contains lazy inference adapters.
- app/core/enum/ defines task types and statuses; app/vector_database/ wraps Qdrant.
- documents/ and app/core/onnx/ are local runtime assets ignored by Git. app/notebooks/ contains model experiments.

## Working rules

1. Read the affected route, schema, service, model, and worker together where behavior crosses those layers.
2. Preserve the existing feature-oriented module layout and public contracts unless the task requires changing them. Keep diffs focused; avoid unrelated reformatting.
3. Prefer explicit types, clear names, explicit imports, small cohesive functions, and visible transaction/error handling in changed code. Existing bugs or inconsistencies are not conventions to reproduce.
4. Check ownership and authorization when a change accepts user, document, or task identifiers. Authentication alone does not establish resource ownership.
5. Treat database columns, JSON keys, task enum values, and API fields as contracts. Renames may require coordinated migration or compatibility handling. For example, finshed_at is the current stored/schema spelling.
6. Follow status handling through success and failure paths. Keep failed work from being reported as finished, and check downstream success before removing source files.
7. Imports of app.main and worker processors are checked to avoid database/Qdrant/model startup. Lifespan startup initializes tables; constructing a Qdrant client performs remote operations, and first inference can load/download models.
8. Keep secret values out of code, documentation, and output. Use configuration variable names when documenting setup. Leave uploaded documents, virtual environments, and model binaries out of routine source scans and edits.
9. Focused unittest regressions and Ruff are configured. Runtime dependencies and poetry.lock cover source imports. No CI or migration framework is configured. Do not present a clean installation, actual inference, or production startup as verified without checking them.
10. Select checks for the requested behavior. Use focused regression tests for meaningful code changes, isolate external services/models, and use disposable data for integration checks. Documentation-only edits need link/content checks, not a new test suite.
11. Update relevant guide facts when the implementation changes. Report what changed, what was verified, and any remaining limits.
