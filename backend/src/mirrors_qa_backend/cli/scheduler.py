import datetime
import time

from mirrors_qa_backend import logger
from mirrors_qa_backend.db import Session
from mirrors_qa_backend.db.mirrors import get_enabled_mirrors
from mirrors_qa_backend.db.tests import create_test, expire_tests, list_tests
from mirrors_qa_backend.db.worker import get_idle_workers
from mirrors_qa_backend.enums import StatusEnum
from mirrors_qa_backend.settings.scheduler import SchedulerSettings


def main(
    sleep_seconds: float = SchedulerSettings.SLEEP_SECONDS,
    expire_tests_since: float = SchedulerSettings.EXPIRE_TEST_SECONDS,
    workers_since: float = SchedulerSettings.IDLE_WORKER_SECONDS,
):
    while True:
        with Session.begin() as session:
            mirrors = get_enabled_mirrors(session)
            # expire tests whose results have not been reported
            expired_tests = expire_tests(
                session,
                interval=datetime.timedelta(seconds=expire_tests_since),
            )
            for expired_test in expired_tests:
                logger.info(
                    f"Expired test {expired_test.id}, "
                    f"country: {expired_test.country_code}, "
                    f"worker: {expired_test.worker_id}"
                )

            idle_workers = get_idle_workers(
                session,
                interval=datetime.timedelta(
                    seconds=workers_since,
                ),
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
                # While we have expired "unreported" tests, it is possible that
                # a test for a mirror might still be PENDING as the interval
                # for expiration and that of the scheduler might overlap.
                # In such scenarios, we skip creating a test for such workers.
                pending_tests = list_tests(
                    session,
                    worker_id=idle_worker.id,
                    statuses=[StatusEnum.PENDING],
                )

                if pending_tests.nb_tests:
                    logger.info(
                        "Skipping creation of new test entries for "
                        f"{idle_worker.id} as {pending_tests.nb_tests} "
                        f"tests are still pending."
                    )
                    continue

                # Create a test for each mirror from the countries the worker registered
                for country in idle_worker.countries:
                    for mirror in mirrors:
                        new_test = create_test(
                            session=session,
                            worker=idle_worker,
                            country_code=country.code,
                            mirror=mirror,
                        )
                        logger.info(
                            f"Created new test {new_test.id} for worker "
                            f"{idle_worker.id} in location {country.name} "
                            f"for mirror {mirror.id}"
                        )

        logger.info(f"Sleeping for {sleep_seconds} seconds.")
        time.sleep(sleep_seconds)
