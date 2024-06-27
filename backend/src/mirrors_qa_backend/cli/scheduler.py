import datetime
import time
from argparse import Namespace

from mirrors_qa_backend import logger
from mirrors_qa_backend.db import Session
from mirrors_qa_backend.db.tests import create_test, expire_tests, list_tests
from mirrors_qa_backend.db.worker import get_idle_workers
from mirrors_qa_backend.enums import StatusEnum
from mirrors_qa_backend.settings.scheduler import SchedulerSettings


def main(args: Namespace):  # noqa: ARG001
    while True:
        with Session.begin() as session:
            # expire tests whose results have not been reported
            expired_tests = expire_tests(
                session,
                interval=datetime.timedelta(
                    seconds=SchedulerSettings.EXPIRE_TEST_SECONDS
                ),
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
                    seconds=SchedulerSettings.IDLE_WORKER_SECONDS
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
                for country in idle_worker.countries:
                    # While we have expired "unreported" tests, it is possible that
                    # a test for a country might still be PENDING as the interval
                    # for expiration and that of the scheduler might overlap.
                    # In such scenarios, we skip creating a test for that country.
                    pending_tests = list_tests(
                        session,
                        worker_id=idle_worker.id,
                        statuses=[StatusEnum.PENDING],
                        country_code=country.code,
                    )

                    if pending_tests.nb_tests:
                        logger.info(
                            "Skipping creation of new test entries for "
                            f"{idle_worker.id} as {pending_tests.nb_tests} "
                            f"tests are still pending for country {country.name}"
                        )
                        continue

                    new_test = create_test(
                        session=session,
                        worker_id=idle_worker.id,
                        country_code=country.code,
                        status=StatusEnum.PENDING,
                    )
                    logger.info(
                        f"Created new test {new_test.id} for worker "
                        f"{idle_worker.id} in country {country.name}"
                    )

        logger.info(
            f"Sleeping for {SchedulerSettings.SCHEDULER_SLEEP_SECONDS} seconds."
        )
        time.sleep(SchedulerSettings.SCHEDULER_SLEEP_SECONDS)
