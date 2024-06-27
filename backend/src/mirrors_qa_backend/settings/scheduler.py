from mirrors_qa_backend.settings import Settings, getenv


class SchedulerSettings(Settings):
    """Scheduler settings"""

    # number of seconds the scheduler sleeps before attempting to create tests
    SCHEDULER_SLEEP_SECONDS = int(
        getenv("SCHEDULER_SLEEP_SECONDS", default=60 * 60 * 3)
    )
    # number of seconds into the past to determine if a worker is idle
    IDLE_WORKER_SECONDS = int(getenv("IDLE_WORKER_SECONDS", default=60 * 60))
    # number of seconds to wait before expiring a test whose data never arrived
    EXPIRE_TEST_SECONDS = int(getenv("EXPIRE_TEST_SECONDS", default=60 * 60 * 24))
