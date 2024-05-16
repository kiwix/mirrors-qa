import datetime
import time
from urllib.parse import urlsplit

import humanfriendly
import requests

TIMEOUT = 5
CHUNK_SIZE = humanfriendly.parse_size("1MiB")
TEST_URL = (
    "https://download.kiwix.org/release/kiwix-tools/kiwix-tools_macos-x86_64.tar.gz"
)
VPN_INTERVAL = 10
TEST_INTERVAL = 60


def fmt(size: int) -> str:
    return humanfriendly.format_size(size, binary=True)


def main():
    print("hello")

    while True:
        print("Ensuring we're on VPN", flush=True)
        try:
            resp = requests.get("https://am.i.mullvad.net/connected", timeout=TIMEOUT)
            resp.raise_for_status()
            print(f"> {resp.text}", flush=True)
            assert "You are connected to Mullvad" in resp.text
        except Exception as exc:
            print(f"Failed to check VPN status: {exc}")
            time.sleep(VPN_INTERVAL)
            continue

        try:
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
            print(f"Speed: {fmt(speed)}/s", flush=True)
        except Exception as exc:
            raise exc
            print(f"Error: {exc}", flush=True)

        time.sleep(TEST_INTERVAL)


if __name__ == "__main__":
    main()
