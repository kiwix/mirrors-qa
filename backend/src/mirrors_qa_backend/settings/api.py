from mirrors_qa_backend.settings import Settings, getenv


class APISettings(Settings):
    """Backend API settings"""

    JWT_SECRET: str = getenv("JWT_SECRET", mandatory=True)
    # number of seconds before a message expire
    MESSAGE_VALIDITY = int(getenv("MESSAGE_VALIDITY", default=60))
    # number of hours before access tokens expire
    TOKEN_EXPIRY = int(getenv("TOKEN_EXPIRY", default=24))
