from sqlalchemy.orm import Session

from app.base.config import WorkerConfig
from app.base.extensions import run_worker_loop
from app.core.enum import WorkerTaskType
from app.database_extension import get_session
from app.models import WorkerTask
from app.services import worker_task_service
from app.workers.worker_task_runner import run_task


class SummarizationWorker:
    def summarization_worker_print(self, text: str) -> None:
        print(f"[SummarizationWorker] {text}")

    def delete_finished_summarization_tasks(self, db: Session) -> None:
        tasks = worker_task_service.get_finished_tasks(db, WorkerTaskType.SUMMARIZATION)
        for task in tasks:
            db.delete(task)
        if tasks:
            db.commit()

    def process_summarization_task(self, db: Session, task: WorkerTask) -> bool:
        raise NotImplementedError("Summarization has no implementation yet")

    def _process_task(self, db: Session, task: WorkerTask) -> bool:
        completed = run_task(
            db, task, lambda: self.process_summarization_task(db, task)
        )
        if not completed:
            self.summarization_worker_print(f"Summarization task {task.id} failed")
        return completed

    def worker_loop(self) -> None:
        self.summarization_worker_print("Starting worker loop")
        run_worker_loop(
            create_session=get_session,
            fetch_task=lambda db: worker_task_service.get_new_task(
                db, WorkerTaskType.SUMMARIZATION
            ),
            process_task=self._process_task,
            cleanup_finished=self.delete_finished_summarization_tasks,
            interval_seconds=WorkerConfig.SUMMARIZATION_POLL_INTERVAL_SECONDS,
            log=self.summarization_worker_print,
        )
