import subprocess
import sys

WORKER_MODULES = (
    "app.workers.ner_worker.ner_worker_processor",
    "app.workers.document_worker.document_worker_processor",
    "app.workers.summarization_worker.summarization_worker_processor",
)


def main() -> None:
    processes: list[subprocess.Popen[bytes]] = []
    try:
        for module in WORKER_MODULES:
            processes.append(subprocess.Popen([sys.executable, "-m", module]))
        for process in processes:
            process.wait()
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            process.wait()


if __name__ == "__main__":
    main()
