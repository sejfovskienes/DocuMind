from .summarization_worker import SummarizationWorker


def main() -> None:
    SummarizationWorker().worker_loop()


if __name__ == "__main__":
    main()
