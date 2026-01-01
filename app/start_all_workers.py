import subprocess
import platform

from app.workers.ner_worker import ner_worker_processor
from app.workers.document_worker import document_worker_processor
from app.workers.summarization_worker import summarization_worker_processor

def main():
    print("Starting all workers...\n\n")
    print("\tStarting NER Worker...")
    ner_worker_processor.main()
    print("\tStarting Document Worker...")
    document_worker_processor.main()
    print("\tStarting Summarization Worker...")
    summarization_worker_processor.main()

if __name__ == "__main__":
    main()


def open_worker_in_new_terminal(command):
    system = platform.system()
    if system == "Windows":
        subprocess.Popen(["start", "cmd", "/k", command], shell=True)
    elif system == "Linux":
        subprocess.Popen(["gnome-terminal", "--", "bash", "-c", command])
    elif system == "Darwin":  # macOS
        subprocess.Popen(["osascript", "-e",
                          f'tell app "Terminal" to do script "{command}"'])
    else:
        print(f"Unsupported OS: {system}")

def main():
    open_worker_in_new_terminal("python -m app.workers.ner_worker")
    open_worker_in_new_terminal("python -m app.workers.document_worker")
    open_worker_in_new_terminal("python -m app.workers.summarization_worker")

if __name__ == "__main__":
    main()