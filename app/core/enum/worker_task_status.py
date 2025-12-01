from enum import Enum

class WorkerTaskStatus(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    FINISHED = "FINISHED"
    FAILED = "FAILED"