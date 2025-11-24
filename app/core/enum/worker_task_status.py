from enum import Enum

class WorkerTaskStatus(Enum):
    QUEUED: 1
    PROCESSING: 2
    FINISHED: 3
    FAILED: 4