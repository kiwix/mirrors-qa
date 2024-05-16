import datetime
from urllib.parse import urlsplit

import humanfriendly
import requests

TIMEOUT = 5
CHUNK_SIZE = humanfriendly.parse_size("1MiB")
TEST_URL = (
    "https://download.kiwix.org/release/kiwix-tools/kiwix-tools_macos-x86_64.tar.gz"
)


def fmt(size: int) -> str:
    return humanfriendly.format_size(size, binary=True)


def check_download_speed():
    print("Testing… ", end="", flush=True)
    finger = requests.head(TEST_URL, timeout=TIMEOUT, allow_redirects=True)
    size = int(finger.headers.get("Content-Length", "0"))
    mirror = urlsplit(finger.url).netloc
    print(f"mirror {mirror} ({fmt(size)})", flush=True)

    start = datetime.datetime.now(tz=datetime.UTC)
    resp = requests.get(url=TEST_URL, timeout=TIMEOUT, stream=True)
    resp.raise_for_status()
    downloaded = 0
    for data in resp.iter_content(CHUNK_SIZE):
        downloaded += len(data)
        pc = downloaded * 100 / size
        print(f"\r{pc:.2f}%: {fmt(downloaded)}/{fmt(size)}", flush=True)
    end = datetime.datetime.now(tz=datetime.UTC)
    duration = end - start
    speed = int(size / duration.total_seconds())
    return speed

