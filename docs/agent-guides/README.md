# DocuMind agent guides

This source review was completed on 2026-10-11 before any requested application changes. Start with [AGENTS.md](../../AGENTS.md) for repository-wide working guidance.

| Guide | Use it for |
| --- | --- |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Finding modules, entry points, data ownership, and feature flows |
| [CODE_CONVENTIONS.md](CODE_CONVENTIONS.md) | Matching existing structure and naming; identifying inconsistencies |
| [CLEAN_CODE.md](CLEAN_CODE.md) | Applying concrete clean-code recommendations to future changes |
| [WORKERS_AND_VALIDATION.md](WORKERS_AND_VALIDATION.md) | Understanding task processing, configuration, dependencies, and checks |

## Reading the findings

Observed facts are tied to repository paths. Inferred preferences describe recurring implementation choices; they are not confirmed personal preferences. Recommendations describe a direction for new work and do not authorize a broad cleanup. Known gaps are source-review findings, not results from running the API or workers.

The review used three smaller-model gpt-6-luna agents for architecture, conventions/clean code, and workers/validation, followed by a primary-agent review. It covered the Python source tree, project metadata, and file inventory. It did not inspect secret values, uploaded document contents, model binaries, or notebook outputs. No external documentation was needed for this repository inventory.

## Before the next change

Read the guide for the affected subsystem and verify its claims against current source. Trace changes across HTTP contracts, schemas, SQL persistence, queue payloads/statuses, and vector storage as needed. Choose validation that exercises the changed behavior without triggering production services or model downloads accidentally.

## Review limits

No application code or dependencies were changed. The API and workers were not started. No automated tests, CI configuration, migration framework, or formatter/linter configuration were found in the reviewed tree; the model-testing notebook is exploratory work. Runtime correctness and dependency completeness remain unverified. Several concrete inconsistencies are documented in the guides for consideration when related work is requested.
