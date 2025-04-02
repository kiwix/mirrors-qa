# mirrors-qa worker

The qa-worker is a probe that fetches Test requests from the API, runs them then uploads results back to the API.

- A Test request is a combination of a Country to test and a Kiwix mirror.
- A test set is composed of hundreds of tests to simulate downloads to all Kiwix mirrors from all supported origin locations.
- Origin locations are based on the wireguard config files listed on the worker's filesystem.
- A Single test is connecting to a country-specified exit node, downloading a 50M file from specified mirror then uploading results to API

## Requirements

- GNU/Linux host.
- Fast internet connexion (downstream).
  - If not fast enough, data will be innacurate. 1Gbps mini.
  - Consumes about 2TB per month.
- Working [Docker CE](https://docs.docker.com/engine/install/).
- The clock must be synchronized, e.g. using ntp.
- A [mirrors-qa](https://mirrors-qa.kiwix.org) Worker ID.
- A 2048b RSA private key with its public key on the user account.
- Wireguard configurations for different countries (see below).


## Setting-up

- Install docker
- Create RSA keypair
- Create config file `/etc/worker.config`
- Create startup script `/usr/local/bin/worker-qa-restart.sh`

### RSA Keypair

```sh
openssl genrsa -out ovh1.pem 2048
openssl rsa -in ovh1.pem -pubout -out ovh1.pub.pem
```

You submit the content of `ovh1.pub.pem` to mirrors-qa admin which will add it (on the server) via:

```sh
# illustration (to be done on server by admin, not on worker)
cat ovh1.pub.pem | mirrors-qa-backend create-worker ovh1
```

### Config file

```sh
# identifier of the worker (must be registered on server)
WORKER_ID="ovh1"
WORKDIR=/data/worker

SLEEP_DURATION="5m"

# the following are not used by the worker
# but by the ProtonVPN config downloader
PROTON_USERNAME="xxxx"
PROTON_PASSWORD="yyyy"
```

### Startup script

```sh
#!/bin/bash

DEBUG=
CONTAINER="qa-worker"
IMAGE="ghcr.io/kiwix/mirrors-qa-worker-manager:latest"
TASK_WORKER_IMAGE="ghcr.io/kiwix/mirrors-qa-task-worker:latest"
SLEEP_DURATION="5m"
WORKDIR=/data/worker
WORKER_ID="notset"
BACKEND_API_URI="https://api.mirrors-qa.kiwix.org"
WIREGUARD_IMAGE="lscr.io/linuxserver/wireguard:1.0.20210914-r4-ls53"

if [ -f /etc/worker.config ]; then
    source /etc/worker.config
fi

# already running?
docker ps |grep $CONTAINER |awk '{print $1}' | while read line ; do
    echo ">stopping worker container $line"
    docker stop $line
    echo ">removing worker container $line"
    docker rm $line
done

docker stop $CONTAINER
docker rm $CONTAINER

echo ">pulling image $IMAGE…"
docker pull $IMAGE

echo ">starting creator worker"
docker run \
    --name $CONTAINER \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v /lib/modules:/lib/modules \
    -v $WORKDIR:/data \
    -v /data/id_rsa:/etc/ssh/keys/id_rsa \
    -e DEBUG=$DEBUG \
    -e BACKEND_API_URI=$BACKEND_API_URI \
    -e SLEEP_DURATION=$SLEEP_DURATION \
    -e WORKER_ID=$WORKER_ID \
    -e TASK_WORKER_IMAGE=$TASK_WORKER_IMAGE \
    -e WIREGUARD_IMAGE=$WIREGUARD_IMAGE \
    --restart unless-stopped \
    --detach \
    $IMAGE \
    mirrors-qa-manager $WORKER_ID

```

Make sure the script is executable: `chmod +x /usr/local/bin/worker-qa-restart.sh`

### Wireguard configs

You are responsible for placing your VPN configuration files in the appropriate location:

- Wireguard only
- Inside `/data/`
- Filename ending in `.conf`
- Filename starting with 2-letters country code followed by a dash (`/[a-z]{2}-.+\.conf/i`)

You can use any Wireguard-copmpatible service. We've tested [Mullvad VPN](https://mullvad.net/en) which is great but are currently using [ProtonVPN](- [ProtonVPN](https://protonvpn.com/) because it supports more countries.

> [!CAUTION]
> ProtonVPN config files needs to be re-downloaded frequently.
> Use the following script and cron task to do it automatically using simply your credentials.

File: `/usr/local/bin/refresh-proton-configs.sh`

```sh
#!/bin/bash

WORKDIR=/data/worker
PROTON_USERNAME="notset"
PROTON_PASSWORD="notset"

if [ -f /etc/worker.config ]; then
    source /etc/worker.config
fi

docker run \
    -it \
    --rm \
    --name proton-config-dl \
    -v $WORKDIR:/data \
    -e USERNAME="${PROTON_USERNAME}" \
    -e PASSWORD="${PROTON_PASSWORD}" \
    ghcr.io/kiwix/mirrors-qa-proton-confdl \
    protonvpn-wireguard-configs -v

```

Make sure it's executable (`chmod +x /usr/local/bin/refresh-proton-configs.sh`)

Have it running daily:

```sh
apt install -y cron
ln -s /usr/local/bin/refresh-proton-configs.sh /etc/cron.daily/refresh_proton
```

## Running

```sh
worker-qa-restart.sh
```

Manage it using Docker

```sh
docker ps
docker logs --tail 50 -f qa-worker
docker stop qa-worker
```
