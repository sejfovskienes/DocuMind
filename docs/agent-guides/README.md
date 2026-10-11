# DocuMind agent guides

Start with [AGENTS.md](../../AGENTS.md) and the standing [project context and behavior](../../.agents/project-context.md). The guides below were reviewed and updated on 2026-10-11 after the requested consistency refactor. Check current source when later changes affect these facts.

| Guide | Use it for |
| --- | --- |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Boundaries, entry points, data flow, and compatibility limits |
| [CODE_CONVENTIONS.md](CODE_CONVENTIONS.md) | Package exports, typing, configuration, and Ruff |
| [CLEAN_CODE.md](CLEAN_CODE.md) | Clean-code recommendations for future changes |
| [WORKERS_AND_VALIDATION.md](WORKERS_AND_VALIDATION.md) | Task lifecycle, environment keys, and offline checks |

The initial source review used three gpt-6-luna agents. The refactor also used three smaller-model agents for workers/models, config/extensions, and routes/services, followed by root review and validation. Observations describe checked source, not production runtime guarantees. Recommendations do not authorize unrelated architecture changes.

Offline regression tests and Ruff are now configured. Real service integration, model inference, CI, data migrations, and crash recovery remain separate work. Secrets, uploaded documents, model binaries, and notebook outputs are excluded from routine scans and edits.
