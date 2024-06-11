from requests import RequestException


class EmptyMirrorsError(Exception):
    """An empty list was used to update the mirrors in the database."""


class MirrorsExtractError(Exception):
    """An error occurred while extracting mirror data from page DOM"""


class MirrorsRequestError(RequestException):
    """A network error occurred while fetching mirrors from the mirrors URL"""
