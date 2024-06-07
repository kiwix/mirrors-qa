import argparse

from mirrors_qa_backend import Settings, db
from mirrors_qa_backend.db import mirrors


def main():
    parser = argparse.ArgumentParser(prog="mirrors-qa-backend")
    parser.add_argument(
        "--update-mirrors",
        action="store_true",
        help=f"Update the list of mirrors from {Settings.mirrors_url}",
    )

    args = parser.parse_args()

    if args.update_mirrors:
        with db.Session.begin() as session:
            mirrors.update_mirrors(session, mirrors.get_current_mirror_countries())


if __name__ == "__main__":
    main()
