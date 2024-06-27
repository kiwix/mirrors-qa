This docker-compose configuration to be used **only** for development purpose.

## List of containers

### backend

This container is a backend web server, linked to its database.
It provides a command `mirrors-qa-backend` to simplify tasks like updating of mirrors.
Run `mirrors-qa-backend --help` in the container to see the sub-commands and options.

### postgresqldb

This container is a PostgreSQL DB. DB data is kept in a volume, persistent across containers restarts.

### scheduler
This container creates test entries for idle workers (i.e workers who have not been seen in the last `IDLE_WORKER_SECONDS` environment variable)

### worker_manager

This container is the main worker container, responsible to start tasks. It is commented by default. Before uncommenting it:

- [Get wireguard configuration files](#get-wireguard-configuration-files)
- [Create a test worker](#create-a-test-worker)
- [Build the task worker image](#build-the-task-image)

## Instructions

**NOTE:** Unless otherwise stated, all the commands are run from the `dev` directory.

First start the Docker-Compose stack:

```sh
cd dev
docker compose up --build
```

### get wireguard configuration files
- Create a `data` directory:
    ```sh
    mkdir data
    ```
    This is the name of the directory used as a bind mount in the compose file.

-  Move the Mullvad configuration files into the `data` directory. Configuration files should be named in the format `<country_code>.conf` where
    `<country_code>` is the ISO 3166-1 alpha-2 code of the country.
    On first time start up, the `worker_manager` will select a random file to start up the `wireguard` container.
    On receiving a task from the backend scheduler, it will search for a configuration file belonging to that task and reconfigure the wireguard container.
    If the configuration file does not exist, it will skip the test.

### create a test worker

- Generate a private key:
    ```sh
    openssl genrsa -out id_rsa 2048
    ```
    The key name `id_rsa` is used as a bind mount in the compose file.

- Assuming the backend service is up, create a worker in the backend:
    ```sh
    docker exec -i mirrors-qa-backend mirrors-qa-backend create-worker --countries=us,fr,ca test_worker < ./id_rsa
    export WORKER_ID=test_worker
    ```

### build the task image
- Build the task worker image.
    ```sh
    cd ../worker/task
    docker build -t mirrors-qa-task-worker .
    export TASK_WORKER_IMAGE=mirrors-qa-task-worker
    ```
