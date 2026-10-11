# Clean-code recommendations

These are recommendations for future changes, not claims about established repository rules or confirmed user preferences. They are based on patterns found in the inspected Python code.

## Keep boundaries clear

- Keep HTTP parsing, authentication, and response shaping in `app/routes/`; keep database operations in `app/services/`; keep ORM definitions in `app/models/`; keep request/response validation in `app/schemas/`.
- Pass dependencies such as a database session explicitly. Avoid loading models, opening database clients, or doing file I/O at import time where practical.
- Keep worker orchestration separate from worker processing, following the existing processor module pattern, and make external clients/model dependencies explicit where practical.

## Make behavior and types clear

- Add accurate parameter and return annotations to public functions. Use `Any` from `typing` when required; avoid the built-in `any` in annotations. Choose one modern annotation style for new code, preferably built-in generics and `T | None` under the declared Python 3.12 minimum.
- Use names that describe the domain object and operation. Avoid shadowing built-ins such as `id` and broad one-letter names where they obscure meaning.
- Keep a function focused on one operation. Extract helpers when they name a real concept or remove repeated logic; avoid wrappers that only add indirection.
- Validate assumptions at boundaries: missing database records, absent configuration, malformed task payloads, and empty collections should have explicit outcomes.
- Prefer structured logging with context for service and worker diagnostics. Do not expose credentials, tokens, or document contents in logs.

## Handle persistence and failures deliberately

- Keep database writes in a clear transaction boundary. Roll back after failed transactions; do not catch an exception only to print it and continue with potentially invalid state.
- Catch the narrowest exception that can be handled meaningfully. Preserve the original cause when raising a higher-level error.
- Keep HTTP-specific exceptions at the API boundary where possible; services should have a consistent, documented error contract rather than mixing HTTP exceptions, booleans, and missing values unpredictably.
- Ensure worker tasks end in the state matching their outcome. Define timestamp semantics for terminal outcomes and avoid marking a task finished after an error.
- Close sessions and external resources reliably using context managers or `try/finally`, including idle worker paths.

## Preserve compatibility and safety

- Treat SQL column names, serialized task payload keys, routes, response fields, and enum values as compatibility surfaces. Renaming requires tracing callers and persisted data.
- Do not change misspelled persisted identifiers such as `finshed_at` as a cleanup-only edit; include a migration and compatibility plan when correcting them.
- Keep secrets in configuration, fail clearly when required configuration is absent, and never put secrets in source or logs.
- Avoid broad behavior changes while refactoring. Separate cleanup from functional changes when that makes review safer.

## Keep code easy to review

- Follow the surrounding module's established architecture and use consistent four-space indentation, readable wrapping, and explicit imports.
- Remove dead imports and commented-out code when touching the relevant section, but avoid unrelated cleanup that obscures the purpose of the change.
- Prefer clear conditional branches over deeply nested control flow. Return early for invalid or absent input where that clarifies the main path.
- Use constants for repeated domain values, but do not create configuration abstractions for one-off values without a concrete need.

## Verification

- This repository currently has no formatter, linter, or test configuration declared in `pyproject.toml`. For future changes, use available project checks when present and add focused tests for behavior changes when the task asks for verification or the risk warrants it. Never claim a check ran unless it did.
