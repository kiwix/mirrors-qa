from requests import RequestException


class MirrorsExtractError(Exception):
    """An error occurred while extracting mirror data from page DOM"""

    pass


class MirrorsRequestError(RequestException):
    """A network error occurred while fetching mirrors from the mirrors URL"""

    pass


class PEMPublicKeyLoadError(Exception):
    """Unable to deserialize a public key from PEM encoded data"""

    pass


class PEMPrivateKeyLoadError(Exception):
    """Unable to deserialize a private key from PEM encoded data"""

    pass
