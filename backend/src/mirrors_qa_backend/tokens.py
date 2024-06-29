import datetime

import jwt

from mirrors_qa_backend.settings.api import APISettings


def generate_access_token(worker_id: str) -> str:
    issue_time = datetime.datetime.now(datetime.UTC)
    expire_time = issue_time + datetime.timedelta(
        seconds=APISettings.TOKEN_EXPIRY_SECONDS
    )
    payload = {
        "iss": "mirrors-qa-backend",  # issuer
        "exp": expire_time.timestamp(),  # expiration time
        "iat": issue_time.timestamp(),  # issued at
        "subject": worker_id,
    }
    return jwt.encode(payload, key=APISettings.JWT_SECRET, algorithm="HS256")
