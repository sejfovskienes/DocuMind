from .document_worker import DocumentWorker


def main() -> None:
    DocumentWorker().worker_loop()


if __name__ == "__main__":
    main()
