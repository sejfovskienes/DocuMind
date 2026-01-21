import time
from functools import wraps
from sqlalchemy.orm import Session

from app.services import task_service
from app.core.enum import worker_task_type, worker_task_status

from app.database import get_session

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
    
    def __exit__(self, 
                 exc_type, 
                 exc_value, 
                 traceback):
        return self
    
    def summarization_worker_print(self, text: str) -> None:
        print("\033[94m {}\033[00m".format(f"[SummarizationWorker] \t{text}"))
    
    def delete_finished_summarization_tasks(self, db: Session) -> None:
        finished_summarization_tasks = task_service.get_finished_tasks(
            db, 
            worker_task_type.WorkerTaskType.SUMMARIZATION
        )
        if len(finished_summarization_tasks) == 0:
            self.summarization_worker_print("[info]\tFound 0 tasks for cleaning")
            return
        for task in finished_summarization_tasks:
            db.delete(task)
        db.commit()
        count_deleted = len(finished_summarization_tasks)
        message = f"\t[info] Deleted: {count_deleted} tasks from database"
        self.summarization_worker_print(message)

    def process_summarization_task(
            self, 
            db: Session, 
            summarization_task) -> bool:
        pass

    def worker_loop(self):
        db = get_session()
        self.summarization_worker_print("Starting worker loop...")
        self.delete_finished_summarization_tasks(db)
        self.summarization_worker_print("Waiting for tasks...")
        while True:
            try: 
                summarization_task = task_service.get_new_task(
                    db, 
                    task_type=worker_task_type.WorkerTaskType.SUMMARIZATION)
                if summarization_task is None:
                    message = "[info] No new summarization tasks found. Entering sleeping mode..."
                    self.summarization_worker_print(message)
                    time.sleep(20)
                    continue
                else:
                    data = {"status": worker_task_status.WorkerTaskStatus.PROCESSING}
                    task_service.update_worker_task(db, summarization_task, data)
                    processing_result = self.process_summarization_task(db, summarization_task)
                    if processing_result:
                        data = {"status": worker_task_status.WorkerTaskStatus.FINISHED}
                        task_service.update_worker_task(db, summarization_task, data)
                    else:
                        data = {"status": worker_task_status.WorkerTaskStatus.FAILED}
                        task_service.update_worker_task(db, summarization_task, data)
            except Exception as e:
                id = summarization_task.id if summarization_task else "N/A"
                message = f"[error] An error occurred in summarization task with id: {id}\n {e}"
                self.summarization_worker_print(message)
