from art import * # noqa
from .summarization_worker import SummarizationWorker

def main ():
    tprint("Summarization Worker") #noqa
    with SummarizationWorker() as worker:
        worker.worker_loop()

if __name__ == "__main__":
    main()