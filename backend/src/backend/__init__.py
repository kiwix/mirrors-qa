from backend.__about__ import __version__


def entrypoint():
    print(f"Hello from backend:{__version__}")  # noqa: T201
