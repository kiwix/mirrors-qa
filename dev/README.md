This docker-compose configuration to be used **only** for development purpose.

## List of services

### backend

This container is a backend web server, linked to its database.
It provides sub-commands to simplify tasks like updating of mirrors.
Run `mirrors-qa-backend --help` in the container to see the various sub-commands and options.

### postgresqldb

This container is a PostgreSQL DB. DB data is kept in a volume, persistent across containers restarts.

### scheduler

This container creates test entries for idle workers (i.e workers who have not been seen in the last `IDLE_WORKER_SECONDS` environment variable)

### task-worker

This container records the speed results for a particular test.

### worker-manager

This container is responsible for starting the task containers, setting up a wireguard interface, collecting the results from the task container and updates the results of the test on the backend API via REST.

## Starting the services

```sh
docker compose up --build
```
The above command only starts the `backend`, `postgresqldb` and `scheduler`
services.

To start the `worker-manager`, [you need to register a worker](#registering-a-worker). Afterwards, run:
```sh
docker compose --profile worker up --build
```

## Registering a Worker

- [Get wireguard configuration files](#get-wireguard-configuration-files)
- [Create a test worker](#create-a-test-worker)


**NOTE:** Unless otherwise stated, all files and commands are with respective to the `dev` directory.


### Get wireguard configuration files

-  Move the [Mullvad](https://mullvad.net/) configuration files into the `data` directory.
    Configuration files should be named in the format `<country_code>.conf` where
    `<country_code>` is the ISO 3166-1 alpha-2 code of the country.
    On start, the `worker-manager` will select a random file to start up the `wireguard` container.
    On receiving a task from the backend scheduler, it will search for a configuration file belonging to that task and reconfigure the wireguard container.
    If the configuration file does not exist, it will skip the test.

## create a test worker

- Generate a private key:
    ```sh
    openssl genrsa -out id_rsa 2048
    ```
    The key name `id_rsa` is used as a bind mount in the compose file for the worker container.

- Generate a public key for creating the worker on the database.
    ```sh
    openssl rsa -in id_rsa -pubout -out pubkey.pem
    ```

- Assuming the backend service is up (`docker compose up backend`), create a worker and assign them a list of countries to test for.
    If no countries are provided, all available countries in the DB wiil be assigned to the worker. You can update the countries using `mirrors-qa-backend update-worker`.

    In this example, we create a worker named `test` to test for mirrors in France, United States and Canada using the public key file
    named `pubkey.pem`.
    ```sh
    docker exec -i mirrors-qa-backend mirrors-qa-backend create-worker --countries=us,fr,ca test < ./pubkey.pem
    ```
- Set the name of the worker to the `WORKER_ID` variable in the `.env` file.

- Start the services with the worker enabled using `docker compose --profile worker up --build`

## Environment variables

**NOTE:** All environment variables with a `_DURATION` suffix accept values that would be valid for [humanfriendly](https://humanfriendly.readthedocs.io/en/latest/api.html#humanfriendly.parse_timespan)

### backend

The `backend` code houses the `scheduler` and the `RESTful API`. The following environment variables are shared by both services:

- `POSTGRES_URI`: PostgreSQL DSN string
- `REQUESTS_TIMEOUT_DURATION`: how long before a request to an external API times out
- `PAGE_SIZE` - number of rows to return from a request which returns a list of items
- `MIRRORS_LIST_URL`: the URL to fetch list of mirrors from.
- `EXCLUDED_MIRRORS`: hostname of mirror URLs to exclude seperated by commas.

### REST API

- `JWT_SECRET`
- `MESSAGE_VALIDITY_DURATION`: how long should the authentication message be considered as valid from when it was signed
- `TOKEN_EXPIRY_DURATION`: how long access tokens should live

### scheduler

- `SCHEDULER_SLEEP_DURATION`: how long the scheduler should sleep after creating tests for idle workers
- `IDLE_WORKER_DURATION`: mark a worker as idle if it hasn't been seen within duration
- `EXPIRE_TEST_DURATION`: expire tests whose results are still pending after duration

### worker-manager

- `SLEEP_DURATION`: how long the manager should sleep before polling the REST API
- `BACKEND_API_URI`
- `DOCKER_SOCKET`
- `PRIVATE_KEY_FILE`: name of private key file
- `DOCKER_CLIENT_TIMEOUT_DURATION`: how long before a connection to the Docker daemon times out
- `DOCKER_API_RETRIES`: how many times to retry requests to the Docker daemon
- `DOCKER_API_RETRY_DURATION`: how long to wait before retrying a failed request
- `WIREGUARD_IMAGE`
- `WIREGUARD_KERNEL_MODULES`: where to load wireguard kernel modules from (default `/lib/modules`)
- `WIREGUARD_HEALTHCHECK_INTERVAL_SECONDS`
- `WIREGUARD_HEALTHCHECK_TIMEOUT_SECONDS`
- `WIREGUARD_HEALTHCHECK_RETRIES`
- `TASK_WORKER_IMAGE`
- `TEST_FILE_PATH`: location of file to run download speed test

## task-worker

- `REQUESTS_TIMEOUT_SECONDS`: how many seconds beore a request times out
