from humanfriendly import parse_timespan

from mirrors_qa_backend.settings import Settings, getenv


class APISettings(Settings):
    """Backend API settings"""

    JWT_SECRET: str = getenv("JWT_SECRET", mandatory=True)
    # number of seconds before a message expire
    MESSAGE_VALIDITY_SECONDS: float = parse_timespan(
        getenv("MESSAGE_VALIDITY_DURATION", default="1m")
    )
    # number of hours before access tokens expire
    TOKEN_EXPIRY_SECONDS: float = parse_timespan(
        getenv("TOKEN_EXPIRY_DURATION", default="6h")
    )

    # number of seconds after which to consider that not having received
    # successful Test is an issue
    UNHEALTHY_NO_TESTS_DURATION_SECONDS: float = parse_timespan(
        getenv("UNHEALTHY_NO_TESTS_DURATION_SECONDS", default="6h")
    )
