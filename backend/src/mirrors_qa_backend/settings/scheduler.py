from humanfriendly import parse_timespan

from mirrors_qa_backend.settings import Settings, getenv


class SchedulerSettings(Settings):
    """Scheduler settings"""

    # number of seconds the scheduler sleeps before attempting to create tests
    SLEEP_SECONDS = parse_timespan(getenv("SCHEDULER_SLEEP_DURATION", default="3h"))
    # number of seconds into the past to determine if a worker is idle
    IDLE_WORKER_SECONDS = parse_timespan(getenv("IDLE_WORKER_DURATION", default="1h"))
    # number of seconds to wait before expiring a test whose data never arrived
    EXPIRE_TEST_SECONDS = parse_timespan(getenv("EXPIRE_TEST_DURATION", default="1d"))
