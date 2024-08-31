# pyright: strict, reportMissingTypeStubs=false, reportUnknownMemberType=false, reportOptionalSubscript=false, reportUnknownVariableType=false, reportUnknownArgumentType=false
import datetime
import json
import random
import re
import shutil
import signal
import sys
import time
from collections.abc import Generator
from enum import Enum
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import pycountry
from docker.errors import APIError
from docker.models.containers import Container, ExecResult
from docker.types import Mount

from mirrors_qa_manager import logger
from mirrors_qa_manager.backend import AuthCredentials, authenticate
from mirrors_qa_manager.backend import query_api as query_backend_api
from mirrors_qa_manager.cryptography import load_private_key_from_path
from mirrors_qa_manager.docker import (
    exec_command,
    get_docker_client,
    query_host_mounts,
    remove_container,
    run_container,
)
from mirrors_qa_manager.settings import Settings


class WgInterfaceStatus(Enum):
    """Status of the Wireguard interface."""

    DOWN = 0
    UP = 1


class WorkerManager:
    """Manager responsible for creating tasks"""

    def __init__(self, worker_id: str) -> None:

        self.worker_id = worker_id
        self.base_dir = Settings.WORKDIR_FPATH

        # Create the directory where this worker will write their data
        self.instance_dir = self.base_dir / worker_id
        self.instance_dir.mkdir(exist_ok=True)

        self.private_key = load_private_key_from_path(Settings.PRIVATE_KEY_FPATH)
        self.docker = get_docker_client()

        self.host_mounts = query_host_mounts(
            self.docker,
            [Settings.WORKDIR_FPATH, Settings.WIREGUARD_KERNEL_MODULES_FPATH],
        )
        self.host_workdir = self.host_mounts[Settings.WORKDIR_FPATH]

        # Create the root directory for binding with the worker's wireguard container
        self.wg_root_dir = self.instance_dir / "wireguard"
        self.wg_root_dir.mkdir(exist_ok=True)

        # Create the directory where the configuration file for the interface
        # will be found.
        # https://github.com/linuxserver/docker-wireguard/blob/master/root/etc/s6-overlay/s6-rc.d/init-wireguard-confs/run#L5
        self.wg_confs_dir = self.wg_root_dir / "wg_confs"
        self.wg_confs_dir.mkdir(exist_ok=True)
        # name of the wireguard interface
        self.wg_interface = "wg0"
        self.wg_healthcheck_cmd = [
            "curl",
            "--interface",
            self.wg_interface,
            "-s",
            "https://am.i.mullvad.net/json",
        ]
        self.wg_interface_status = WgInterfaceStatus.DOWN
        # commands for bringing down/up the interface whenever a new configuration
        # file is added
        self.wg_down_cmd = ["wg-quick", "down", self.wg_interface]
        self.wg_up_cmd = ["wg-quick", "up", self.wg_interface]

        self.task_container_names = set()
        # location of the test file on the from the mirror's root

        self.auth_credentials: None | AuthCredentials = None

        # register exit signals
        self.register_signals()

    def get_host_fpath(self, container_fpath: Path) -> Path:
        """Determine the host path of a path in the container."""
        return self.host_workdir / container_fpath.relative_to(Settings.WORKDIR_FPATH)

    def get_country_codes_from_config_files(self) -> list[str]:
        """Get the ISO country codes using configuration files in base_dir.

        Finds all files ending with .conf and applies the following steps:
        - take the first two letters of the config filename.
        - add to output list if first two letters of config are valid country codes.
        """
        conf_file_ptn = re.compile(r"^(?P<country_code>[a-z]{2})-")
        country_codes = set()

        for conf_file in self.base_dir.glob("*.conf"):
            if match := conf_file_ptn.search(conf_file.stem):
                country_code = match.groupdict()["country_code"]
                if pycountry.countries.get(alpha_2=country_code):
                    country_codes.add(country_code)

        return list(country_codes)

    def copy_wireguard_conf_file(self, conf_fpath: Path) -> Path:
        """Copy configuration file to wireguard configuration folder."""
        # Move the configuration file to the wg_confs folder of the wireguard
        # container.
        return shutil.copy(
            conf_fpath,
            self.wg_confs_dir / f"{self.wg_interface}.conf",
        )

    def wg_container_is_healthy(self) -> ExecResult | None:
        """Check if a healthcheck command was successful on container."""
        try:
            return exec_command(
                self.docker,
                Settings.WIREGUARD_CONTAINER_NAME,
                self.wg_healthcheck_cmd,
            )
        except APIError as exc:
            logger.error(f"error whlie performing healthcheck: {exc!s}")
            return None

    def wg_healthcheck_untill_healthy(
        self, conf_fpaths: list[Path]
    ) -> ExecResult | None:
        """Try wg healthcheck till status is healthy using configuration files."""
        for conf_fpath in conf_fpaths:
            # Copy the configuration file to the confs folder
            self.copy_wireguard_conf_file(conf_fpath)
            # After copying the file, restart the interface.
            if self.wg_interface_status == WgInterfaceStatus.UP:
                try:
                    exec_command(
                        self.docker,
                        Settings.WIREGUARD_CONTAINER_NAME,
                        self.wg_down_cmd,
                    )
                except APIError as exc:
                    logger.debug(
                        f"error while bringing down wireguard interface: {exc!s}"
                    )
                    pass
                else:
                    self.wg_interface_status = WgInterfaceStatus.DOWN

            if self.wg_interface_status == WgInterfaceStatus.DOWN:
                try:
                    exec_command(
                        self.docker,
                        Settings.WIREGUARD_CONTAINER_NAME,
                        self.wg_up_cmd,
                    )
                except APIError as exc:
                    logger.debug(f"error while bringing up wireguard interface {exc!s}")
                    pass
                else:
                    self.wg_interface_status = WgInterfaceStatus.UP

            logger.debug(f"Checking wireguard interface status using {conf_fpath.name}")

            if healthcheck_result := self.wg_container_is_healthy():
                return healthcheck_result
        return None

    def start_wireguard_container(self, image_name: str, conf_fpath: Path) -> Container:
        #  Try and remove container if it wasn't removed before
        self.remove_container(Settings.WIREGUARD_CONTAINER_NAME)
        self.copy_wireguard_conf_file(conf_fpath)
        # Mount the wireguard directories using the host's fs, not this container's
        mounts = [
            Mount("/config", str(self.get_host_fpath(self.wg_root_dir)), type="bind"),
        ]
        if wg_modules_fpath := self.host_mounts.get(
            Settings.WIREGUARD_KERNEL_MODULES_FPATH
        ):
            mounts.append(Mount("/lib/modules", str(wg_modules_fpath), type="bind"))

        return run_container(
            self.docker,
            image_name,
            name=Settings.WIREGUARD_CONTAINER_NAME,
            cap_add=["NET_ADMIN", "SYS_MODULE"],
            healthcheck={
                "test": ["CMD", *self.wg_healthcheck_cmd],
                "interval": Settings.WIREGUARD_HEALTHCHECK_NANOSECONDS,
                "timeout": Settings.WIREGUARD_HEALTHCHECK_TIMEOUT_NANOSECONDS,
                "retries": Settings.WIREGUARD_HEALTHCHECK_RETRIES,
            },
            ports={
                f"{Settings.WIREGUARD_PORT}/udp": None
            },  # Let the host assign a random port
            sysctls={"net.ipv4.conf.all.src_valid_mark": 1},
            environment={
                "PUID": 1000,
                "PGID": 1000,
                "TZ": "Etc/UTC",
            },
            mounts=mounts,
            detach=True,
            restart_policy={
                "Name": "on-failure",
                "MaximumRetryCount": Settings.WIREGUARD_HEALTHCHECK_RETRIES,
            },
        )

    def start_task_container(
        self,
        image_name: str,
        container_name: str,
        output_filename: str,
        test_file_url: str,
    ) -> Container:
        mounts = [
            Mount("/data", str(self.get_host_fpath(self.instance_dir)), type="bind")
        ]
        return run_container(
            self.docker,
            image_name,
            name=container_name,
            environment={
                "DEBUG": Settings.DEBUG,
            },
            mounts=mounts,
            network_mode=f"container:{Settings.WIREGUARD_CONTAINER_NAME}",
            command=["mirrors-qa-task", test_file_url, f"--output={output_filename}"],
        )

    def query_api(
        self,
        endpoint: str,
        method: str = "get",
        *,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if self.auth_credentials is None:
            self.auth_credentials = authenticate(self.private_key, self.worker_id)

        if self.auth_credentials.expires_in <= datetime.datetime.now():
            self.auth_credentials = authenticate(self.private_key, self.worker_id)

        req_headers = {
            "Authorization": f"Bearer {self.auth_credentials.access_token}",
        }
        return query_backend_api(
            endpoint,
            method,
            headers=req_headers,
            payload=payload,
        )

    def merge_data(
        self, *, ip_data: dict[str, Any], metrics_data: dict[str, Any]
    ) -> dict[str, Any]:
        return {
            **metrics_data,
            "ip_address": ip_data["ip"],
            "city": ip_data["city"],
            "isp": ip_data["organization"],
        }

    def update_countries_list(self):
        """Update the list of countries from config files if there are any."""
        country_codes = self.get_country_codes_from_config_files()
        if not country_codes:
            logger.info("No country codes inferred from configuration files.")
            return

        logger.info(
            f"Found {len(country_codes)} country codes from configuration files."
        )
        logger.debug("Updating list of countries on Backend API.")
        data = self.query_api(
            f"/workers/{self.worker_id}/countries",
            method="put",
            payload={"country_codes": country_codes},
        )
        logger.info(
            f"Updated the list of countries for worker to {len(data['countries'])} "
            "countries."
        )

    def fetch_tests(self) -> Generator[dict[str, str], None, None]:
        logger.debug("Fetching tasks from backend API")
        # Fetch tasks that were assigned to the worker that haven't been expired
        params = urlencode({"worker_id": self.worker_id, "status": "PENDING"})
        while True:
            data = self.query_api(f"/tests?{params}")
            nb_tests = data["metadata"]["page_size"]
            if nb_tests == 0:  # No more pending tests to fetch
                break

            logger.info(f"Fetched {nb_tests} test(s) from Backend API")

            current_page = data["metadata"]["current_page"]
            last_page = data["metadata"]["last_page"]

            logger.debug(
                f"Fetched page {current_page} of {last_page} of pending tests."
            )

            yield from data["tests"]

            if current_page == last_page:
                break

    def sleep(self) -> None:
        logger.info(f"Sleeping for {Settings.SLEEP_SECONDS}s")
        time.sleep(Settings.SLEEP_SECONDS)

    def get_country_code(self, country_name: str) -> str:
        country: Any = pycountry.countries.search_fuzzy(country_name)[0]
        return country.alpha_2.lower()

    def run(self) -> None:
        logger.info("Starting worker manager.")
        # First time startup, get all available configuration files.
        conf_fpaths = self.base_dir.glob("*.conf")
        try:
            # Fetch the first configuration file for starting the container.
            conf_fpath = next(conf_fpaths)
        except StopIteration as exc:
            # no configuration files were found
            message = f"No wireguard configuration file was found in {self.base_dir}"
            raise FileNotFoundError(message) from exc
        # Start the wireguard network container
        logger.info(f"Starting wireguard container using {conf_fpath.name}.")
        self.start_wireguard_container(Settings.WIREGUARD_IMAGE, conf_fpath=conf_fpath)
        # When we start the container with the configuration file for the first
        # time, the interface status is going to be UP. We keep track of this
        # status before performing healthchecks on the container.
        self.wg_interface_status = WgInterfaceStatus.UP
        while True:
            try:
                # Ensure the wireguard container is still up
                if not self.wg_container_is_healthy():
                    # Try all the availalbe configuration files till container is up.
                    if self.wg_healthcheck_untill_healthy(list(conf_fpaths)) is None:
                        error_message = "Unable to start wireguard container."
                        raise Exception(error_message)

                # Update the worker list of countries using the configuration files
                self.update_countries_list()

                for test in self.fetch_tests():
                    test_id = test["id"]
                    country_code = test["country_code"]
                    # Fetch all configuration files for the requested country
                    conf_fpaths = list(self.base_dir.glob(f"{country_code}*.conf"))
                    if not conf_fpaths:
                        logger.error(
                            f"Could not find any configuration file for {country_code}"
                            f"test {test_id}. Skipping test."
                        )
                        continue
                    # Shuffle the order of the configuration files so we don't
                    # always test with the same configuration file.
                    random.shuffle(conf_fpaths)

                    logger.info(
                        f"Reconfiguring wireguard network interface for {country_code}"
                    )

                    healthcheck_result = self.wg_healthcheck_untill_healthy(conf_fpaths)
                    if healthcheck_result is None:
                        logger.error(
                            "error while pefroming wireguard healthcheck for "
                            f"test {test_id}, country: {country_code}"
                        )
                        continue

                    logger.debug(f"Healthcheck result: {healthcheck_result.output}")

                    # Start container for the task
                    task_container_name = f"task-worker-{test_id}"
                    # It is possible that a container with the existing name already
                    # exists, perhaps, due to the task failing and cleanup did not
                    # complete properly.
                    try:
                        self.remove_container(task_container_name)
                    except Exception as exc:
                        logger.error(
                            "error while removing task container "
                            f"{task_container_name}, {exc!s}"
                        )
                        continue

                    logger.info(
                        f"Starting container {task_container_name!r} for "
                        f"processing test {test_id}"
                    )
                    output_fpath = self.instance_dir / f"{test_id}.json"
                    test_file_url = (
                        test["mirror_url"].rstrip("/")
                        + "/"
                        + Settings.TEST_FILE_PATH.lstrip("/")
                    )
                    try:
                        self.task_container_names.add(task_container_name)
                        self.start_task_container(
                            Settings.TASK_WORKER_IMAGE,
                            task_container_name,
                            output_filename=output_fpath.name,
                            test_file_url=test_file_url,
                        )
                    except Exception as exc:
                        logger.error(
                            f"error while setting up container for test {test_id} "
                            f"country: {country_code}: {exc!s}"
                        )
                        continue

                    try:
                        self.remove_container(task_container_name)
                    except Exception as exc:
                        logger.error(
                            "error while removing task container "
                            f"{task_container_name}, {exc!s}"
                        )
                    else:
                        self.task_container_names.remove(task_container_name)

                    results = output_fpath.read_text()
                    logger.info(
                        f"Successfully retrieved metrics results for test {test_id}"
                    )
                    ip_data = json.loads(healthcheck_result.output.decode("utf-8"))
                    payload = self.merge_data(
                        ip_data=ip_data,
                        metrics_data=json.loads(results),
                    )
                    logger.info(f"Uploading results for {test_id} to Backend API")
                    try:
                        self.query_api(
                            f"/tests/{test_id}", method="patch", payload=payload
                        )
                    except Exception as exc:
                        logger.error(
                            f"error while uploading results to Backend API: {exc!s}"
                        )
                        continue
                    finally:
                        output_fpath.unlink()
                    logger.info(f"Uploaded results for {test_id} to Backend API")
            except Exception as exc:
                logger.error(f"error while processing tasks {exc!s}")

            self.sleep()

    def remove_container(
        self, container_name: str, *, force: bool = True, not_found_ok: bool = True
    ) -> None:
        return remove_container(
            self.docker, container_name, force=force, not_found_ok=not_found_ok
        )

    def exit_gracefully(self, *args: Any, **kwargs: Any) -> None:  # noqa: ARG002
        # Ensure there is still a connection to Docker
        self.docker.ping()
        exit_code = kwargs.pop("exit_code", 0)

        logger.info("Removing wireguard container")
        self.remove_container(Settings.WIREGUARD_CONTAINER_NAME)

        # Remove any task containers that were not removed
        for container_name in self.task_container_names:
            self.remove_container(container_name)

        logger.info("Closing Docker client.")
        self.docker.close()

        sys.exit(exit_code)

    def register_signals(self) -> None:
        logger.info("registering exit signals")
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)
        signal.signal(signal.SIGQUIT, self.exit_gracefully)
