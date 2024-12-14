import os
import re
import time
import toml
import logging
import requests
import subprocess
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)


def run(command):
    return os.system(command)


def aria2c_download(urls, directory):
    if run(f"aria2c -c -s 8 -x 8 -k 1M -j 1 -Z --dir {directory} {urls}") == 0:
        logging.info(f"Downloaded {urls} successfully")
    else:
        raise Exception(f"Failed to download {urls}")


def read_config(section, key, filename="config.toml"):
    with open(filename, "r") as f:
        return toml.load(f)[section][key]


def save_config(section, key, value, filename="config.toml"):
    config = {}
    if os.path.exists(filename):
        with open(filename, "r") as f:
            config = toml.load(f)
    config.setdefault(section, {})[key] = value
    with open(filename, "w") as f:
        toml.dump(config, f)


def lineage_download(device_code):
    res = requests.get(
        f"https://download.lineageos.org/api/v2/devices/{device_code}/builds"
    ).json()[0]
    remote_timestamp = res["datetime"]

    try:
        local_timestamp = int(read_config("data", "timestamp"))
        if local_timestamp >= remote_timestamp:
            raise Exception(f"LineageOS for {device_code} hasn't been updated yet")
    except FileNotFoundError:
        logging.info("config.toml not found, creating a new one")
    save_config("data", "timestamp", remote_timestamp)

    urls = " ".join(
        file["url"]
        for file in res["files"]
        if file["filename"] not in {"vbmeta.img", "super_empty.img"}
    )
    sha256 = {
        file["filename"]: file["sha256"]
        for file in res["files"]
        if file["filename"] not in {"vbmeta.img", "super_empty.img"}
    }

    aria2c_download(urls, "tmp")
    logging.info(sha256)


def wait_until_string_appears(command, target_string, interval=1):
    while True:
        result = subprocess.run(command, text=True, capture_output=True)
        if target_string in result.stdout:
            logging.debug("Target string appeared")
            break
        time.sleep(interval)


def clear_tmp():
    for root, dirs, files in os.walk("tmp/", topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir("tmp/")


def lineage_flash():
    files = os.listdir("tmp")
    boot = next((f for f in files if "boot.img" in f), None)
    recovery = next((f for f in files if "recovery.img" in f), None)
    lineage_zip = next(
        (f for f in files if "lineage-" in f and f.endswith(".zip")), None
    )

    if not boot or not recovery:
        raise FileNotFoundError("Required image files not found in tmp/")

    logging.info("Boot into fastboot mode now")
    wait_until_string_appears(["fastboot", "devices"], "fastboot")
    run(f"fastboot flash boot tmp/{boot}")
    run(f"fastboot flash recovery tmp/{recovery}")

    logging.info("Reboot to recovery mode and open adb sideload")
    wait_until_string_appears(["adb", "devices"], "\tsideload")
    run(f"adb sideload tmp/{lineage_zip}")

    clear_tmp()


def lineage_with_microG_download(device_code):
    html = requests.get(f"https://download.lineage.microg.org/{device_code}/").text
    soup = BeautifulSoup(html, "html.parser")

    links = [a["href"] for a in soup.select("td > a")]
    dates = {match.group() for link in links if (match := re.search(r"\d{8}", link))}

    if not dates:
        logging.error("No valid dates found in links")
        return

    latest_date = max(dates)
    download_urls = [
        f"https://download.lineage.microg.org/{device_code}/{link[2:]}"
        for link in links
        if latest_date in link
        and all(
            excl not in link for excl in {".sha256sum", "super_empty.img", "vbmeta.img"}
        )
    ]

    aria2c_download(" ".join(download_urls), "tmp")


if __name__ == "__main__":
    lineage_download("polaris")
    # lineage_with_microG_download("polaris")
    lineage_flash()
    logging.info("Done.")
