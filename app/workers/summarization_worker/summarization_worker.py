from functools import wraps
from sqlalchemy.orm import Session

from app.services import task_service
from app.core.enum import worker_task_type

def singleton(cls):
    instances = {}

    @wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
            return instances[cls]
    return get_instance

@singleton
class SummarizationWorker:
    def __init__(self):
        pass

    def __enter__(self):
        return self 
    
    def __exit__(self):
        return self
    
    def summarization_worker_print(self, text: str) -> None:
        print("\033[94m {}\033[00m".format(f"[SummarizationWorker] \t{text}"))
    
    def delete_finished_summarization_tasks(self, db: Session) -> None:
        finished_summarization_tasks = task_service.get_finished_tasks(
            db, 
            worker_task_type.WorkerTaskType.SUMMARIZATION
        )
        if len(finished_summarization_tasks) == 0:
            self.summarization_worker_print("print in: delete_finished_summarization[info]\tFound 0 tasks for cleaning")
            return
        for task in finished_summarization_tasks:
            db.delete(task)
        db.commit()
        count_deleted = len(finished_summarization_tasks)
        message = f"print in: delete_finished_summarization2[info]\tDeleted: {count_deleted} tasks from database"
        self.summarization_worker_print(message)

    def worker_loop(self):
        self.summarization_worker_print("Starting worker loop...")

        pass