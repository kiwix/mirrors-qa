import datetime
import time

from mirrors_qa_backend import logger
from mirrors_qa_backend.db import Session, tests, worker
from mirrors_qa_backend.enums import StatusEnum
from mirrors_qa_backend.settings import Settings


def main():
    while True:
        with Session.begin() as session:
            # expire tesst whose results have not been reported
            expired_tests = tests.expire_tests(
                session,
                interval=datetime.timedelta(hours=Settings.EXPIRE_TEST_INTERVAL),
            )
            for expired_test in expired_tests:
                logger.info(
                    f"Expired test {expired_test.id}, "
                    f"country: {expired_test.country}, "
                    f"worker: {expired_test.worker_id}"
                )

            idle_workers = worker.get_idle_workers(
                session,
                interval=datetime.timedelta(hours=Settings.IDLE_WORKER_INTERVAL),
            )
            if not idle_workers:
                logger.info("No idle workers found.")

            # Create tests for the countries the worker is responsible for..
            for idle_worker in idle_workers:
                if not idle_worker.countries:
                    logger.info(
                        f"No countries registered for idle worker {idle_worker.id}"
                    )
                    continue
                for country in idle_worker.countries:
                    # While we have expired "unreported" tests, it is possible that
                    # a test for a country might still be PENDING as the interval
                    # for expiration and that of the scheduler might overlap.
                    # In such scenarios, we skip creating a test for that country.
                    pending_tests = tests.list_tests(
                        session,
                        worker_id=idle_worker.id,
                        statuses=[StatusEnum.PENDING],
                        country=country.name,
                    )

                    if pending_tests.nb_tests:
                        logger.info(
                            "Skipping creation of new test entries for "
                            f"{idle_worker.id} as {pending_tests.nb_tests} "
                            "tests are still pending."
                        )
                        continue

                    new_test = tests.create_test(
                        session=session,
                        worker_id=idle_worker.id,
                        country=country.name,
                        status=StatusEnum.PENDING,
                    )
                    logger.info(
                        f"Created new test {new_test.id} for worker "
                        f"{idle_worker.id} in country {country.name}"
                    )

        sleep_interval = datetime.timedelta(
            hours=Settings.SCHEDULER_SLEEP_INTERVAL
        ).total_seconds()

        logger.info(f"Sleeping for {sleep_interval} seconds.")
        time.sleep(sleep_interval)
