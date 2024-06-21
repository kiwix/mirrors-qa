class RecordDoesNotExistError(Exception):
    """A database record does not exist."""

    def __init__(self, message: str, *args: object) -> None:
        super().__init__(message, *args)


class EmptyMirrorsError(Exception):
    """An empty list was used to update the mirrors in the database."""


class DuplicatePrimaryKeyError(Exception):
    """A database record with the same primary key exists."""
