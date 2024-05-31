from worker.__about__ import __version__


def entrypoint():
    print(f"Hello from worker:{__version__}")  # noqa: T201
