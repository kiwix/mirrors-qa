# pyright: strict, reportMissingTypeStubs=false, reportUnknownMemberType=false, reportOptionalSubscript=false, reportUnknownVariableType=false, reportUnknownArgumentType=false
import datetime
import json
import shutil
import signal
import sys
import time
from enum import Enum
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlsplit

import pycountry
from docker.models.containers import Container
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
        self.test_file_path: str = urlsplit(Settings.TEST_FILE_URL).path

        self.auth_credentials: None | AuthCredentials = None

        # register exit signals
        self.register_signals()

    def get_host_fpath(self, container_fpath: Path) -> Path:
        """Determine the host path of a path in the container."""
        return self.host_workdir / container_fpath.relative_to(Settings.WORKDIR_FPATH)

    def copy_wireguard_conf_file(self, country_code: str | None = None) -> Path:
        """Path to copied-from-base-dir <country_code>.conf file in instance  directory.

        If country_code is None, first file with .conf suffix is copied.
        Raises:
            FileNotFoundError: configuration file was not found.
        """
        conf_name = None

        if country_code:
            conf_name = f"{country_code}.conf"
        else:
            try:
                conf_name = (next(self.base_dir.glob("*.conf"))).name
            except StopIteration:
                pass

        if conf_name is None:
            if not country_code:
                message = (
                    f"No wireguard configuration file was found in {self.base_dir}"
                )
            else:
                message = (
                    f"Configuration file {country_code}.conf was not "
                    f"found in {self.base_dir}"
                )
            raise FileNotFoundError(message)

        # Move the configuration file to the wg_confs folder of the wireguard
        # container.
        return shutil.copy(
            self.base_dir / conf_name,
            self.wg_confs_dir / f"{self.wg_interface}.conf",
        )

    def start_wireguard_container(self, image_name: str) -> Container:
        # Copy the first configuration file we see during start up by passing
        # no argument. Ensures configuration files actuallly exist before starting
        # the wireguard container
        self.copy_wireguard_conf_file()
        #  Try and remove container if it wasn't removed before
        self.remove_container(Settings.WIREGUARD_CONTAINER_NAME)
        logger.info("Starting wireguard container")
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
            ports={"51820/udp": None},  # Let the host assign a random port
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
                "TEST_FILE_URL": test_file_url,
            },
            mounts=mounts,
            network_mode=f"container:{Settings.WIREGUARD_CONTAINER_NAME}",
            command=["mirrors-qa-task", f"--output={output_filename}"],
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

    def fetch_tests(self) -> list[dict[str, Any]]:
        logger.debug("Fetching tasks from backend API")

        # Fetch tasks that were assigned to the worker that haven't been expired
        params = urlencode({"worker_id": self.worker_id, "status": "PENDING"})
        data = self.query_api(f"/tests?{params}")

        logger.info(f"Fetched {data['metadata']['page_size']} test(s) from Backend API")

        return data["tests"]

    def sleep(self) -> None:
        logger.info(f"Sleeping for {Settings.SLEEP_SECONDS}s")
        time.sleep(Settings.SLEEP_SECONDS)

    def get_country_code(self, country_name: str) -> str:
        country: Any = pycountry.countries.search_fuzzy(country_name)[0]
        return country.alpha_2.lower()

    def run(self) -> None:
        logger.info("Starting worker manager.")
        # Start the wireguard network container
        self.start_wireguard_container(Settings.WIREGUARD_IMAGE)
        while True:
            try:
                # Ensure the wireguard container is still up
                if (
                    exec_command(
                        self.docker,
                        Settings.WIREGUARD_CONTAINER_NAME,
                        self.wg_healthcheck_cmd,
                    ).exit_code
                    == 0
                ):
                    self.wg_interface_status = WgInterfaceStatus.UP

                tests = self.fetch_tests()
                for test in tests:
                    test_id = test["id"]
                    country_code = test["country_code"]
                    # Fetch the configuration file for the requested country
                    try:
                        self.copy_wireguard_conf_file(country_code)
                    except FileNotFoundError:
                        logger.error(
                            f"Could not find {country_code}.conf for "
                            f"test {test_id}. Skipping test."
                        )
                        continue
                    except Exception:
                        logger.error(
                            f"error while fetching {country_code}.conf for {test_id}"
                        )
                        continue

                    logger.info(
                        f"Reconfiguring wireguard network interface for {country_code}"
                    )

                    # After copying the file, restart the interface.
                    if self.wg_interface_status == WgInterfaceStatus.UP:
                        logger.info(
                            f"Bringing down wireguard interface for test {test_id} "
                            f"country_code: {country_code}"
                        )
                        try:
                            exec_command(
                                self.docker,
                                Settings.WIREGUARD_CONTAINER_NAME,
                                self.wg_down_cmd,
                            )
                        except Exception as exc:
                            logger.error(
                                f"error while bringing down wireguard interface  "
                                f"for test {test_id}, country: {country_code}: {exc!s}"
                            )
                            continue
                        else:
                            self.wg_interface_status = WgInterfaceStatus.DOWN

                    if self.wg_interface_status == WgInterfaceStatus.DOWN:
                        logger.info(
                            f"Bringing up wireguard interface for test {test_id}, "
                            f"country_code: {country_code}"
                        )
                        try:
                            exec_command(
                                self.docker,
                                Settings.WIREGUARD_CONTAINER_NAME,
                                self.wg_up_cmd,
                            )
                        except Exception as exc:
                            logger.error(
                                f"error while bringing up wireguard interface "
                                f"for test {test_id}, country: {country_code}: "
                                f"{exc!s}"
                            )
                            continue
                        else:
                            self.wg_interface_status = WgInterfaceStatus.UP

                    # Perform another healthcheck to ensure traffic can go
                    # through.
                    logger.info(
                        "Checking if traffic can pass through wireguard interface "
                        f"for test {test_id}, country: {country_code}"
                    )
                    try:
                        healthcheck_result = exec_command(
                            self.docker,
                            Settings.WIREGUARD_CONTAINER_NAME,
                            self.wg_healthcheck_cmd,
                        )
                    except Exception as exc:
                        logger.error(
                            "error while pefroming wireguard healthcheck for "
                            f"test {test_id}, country: {country_code}, {exc!s}"
                        )
                        continue

                    # Ensure the country that this IP belongs to is the same as the
                    # requested country code.
                    ip_data = json.loads(healthcheck_result.output.decode("utf-8"))
                    ip_country_code = self.get_country_code(ip_data["country"])

                    if ip_country_code != country_code:
                        logger.warning(
                            "Test expects configuration file for "
                            f"{country_code}, got {ip_country_code} from host. "
                            f"Skipping test {test_id} due to wrong "
                            "configuration file."
                        )
                        continue

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
                        + self.test_file_path.lstrip("/")
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
