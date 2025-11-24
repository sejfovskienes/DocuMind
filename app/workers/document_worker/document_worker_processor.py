from art import * # noqa

from .document_worker import DocumentWorker

def main():
    document_worker = DocumentWorker()
    document_worker.worker_loop()

if __name__ == "__main__":
    tprint("DocumentWorker") # noqa
    main()