"""Shared worker polling and session lifecycle."""

from collections.abc import Callable
from time import sleep


def run_worker_loop[SessionT, TaskT](
    create_session: Callable[[], SessionT],
    fetch_task: Callable[[SessionT], TaskT | None],
    process_task: Callable[[SessionT, TaskT], object],
    cleanup_finished: Callable[[SessionT], None],
    interval_seconds: float,
    log: Callable[[str], None],
    sleep_fn: Callable[[float], None] = sleep,
) -> None:
    """Poll tasks continuously, closing each database session after one pass."""
    if interval_seconds < 0:
        raise ValueError("interval_seconds cannot be negative.")

    session = create_session()
    try:
        cleanup_finished(session)
    finally:
        session.close()

    while True:
        session = create_session()
        task = None
        should_sleep = False
        try:
            task = fetch_task(session)
            if task is None:
                should_sleep = True
            else:
                process_task(session, task)
        except Exception as error:
            log(f"Worker iteration failed ({type(error).__name__}).")
            should_sleep = True
        finally:
            session.close()
        if should_sleep:
            sleep_fn(interval_seconds)
