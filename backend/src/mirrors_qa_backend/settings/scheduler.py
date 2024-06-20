from mirrors_qa_backend.settings import Settings, getenv


class SchedulerSettings(Settings):
    """Scheduler settings"""

    # number of hours the scheduler sleeps before attempting to create tests
    SCHEDULER_SLEEP_HOURS = int(getenv("SCHEDULER_SLEEP_INTERVAL", default=3))
    # number of hours into the past to determine if a worker is idle
    IDLE_WORKER_HOURS = int(getenv("IDLE_WORKER_INTERVAL", default=1))
    # number of hours to wait before expiring a test whose data never arrived
    EXPIRE_TEST_HOURS = int(getenv("EXPIRE_TEST_INTERVAL", default=24))
