from bs4 import BeautifulSoup
import re
import requests
import time
import toml
import subprocess
import logging
import os

logging.basicConfig(level=logging.INFO)


def run(command):
    return os.system(command)


def aria2c_download(url: str, dir: str):
    if run(f"aria2c -c -s 8 -x 8 -k 1M -j 1 -Z --dir {dir} {url}") == 0:
        print(f"Downloaded {url} successfully")
    else:
        raise Exception(f"Faield to download {url}")


def read_config(section, key, filename="config.toml"):
    with open(filename, "r") as f:
        config = toml.load(f)
        return config[section][key]


def save_config(section, key, value, filename="config.toml"):
    try:
        with open(filename, "r+") as f:
            config = toml.load(f)
            f.seek(0, 0)  # move the cursor to the beginning of the file
            config[section][key] = value
            toml.dump(config, f)
    except FileNotFoundError:
        with open(filename, "w") as f:
            toml.dump({section: {key: value}}, f)


def lineage_download(device_code):
    res = requests.get(
        f"https://download.lineageos.org/api/v2/devices/{device_code}/builds"
    ).json()[0]
    timestamp_remote = res["datetime"]
    try:
        timestamp_local = read_config("data", "timestamp")
        if int(timestamp_local) >= timestamp_remote:
            raise Exception(f"LineageOS for {device_code} hasn't been updated yet")
    except FileNotFoundError:
        print("config.toml not found, now create a new one")
        save_config("data", "timestamp", timestamp_remote)
    urls = ""
    sha256 = {}
    for i in res["files"]:
        if i["filename"] != "vbmeta.img" and i["filename"] != "super_empty.img":
            print(i["filename"])
            urls += i["url"] + " "
            sha256[i["filename"]] = i["sha256"]
    aria2c_download(urls, "tmp")
    # todo: sha256
    print(sha256)


def wait_until_string_appears(command, target_string, interval=1):
    """
    循环调用外部程序，直到输出中包含目标字符串。

    :param command: list，外部程序的命令及参数，例如 ["ping", "127.0.0.1", "-c", "1"]。
    :param target_string: str，目标字符串。
    :param interval: int，重复调用之间的间隔时间（秒）。
    :return: None
    """
    while True:
        # 调用外部程序并捕获输出
        result = subprocess.run(command, text=True, capture_output=True)

        logging.debug(result.stdout.strip())

        if target_string in result.stdout:
            logging.debug("\n目标字符串已出现")
            break

        time.sleep(interval)


def rm_tmp():
    for root, dirs, files in os.walk("tmp/"):
        for n in files:
            os.remove(os.path.join(root, n))
        for n in dirs:
            os.rmdir(os.path.join(root, n))
        os.rmdir(root)


def lineage_flash():
    files = os.listdir("tmp")
    boot_filename = None
    recovery_filename = None
    lineage_zip_filename = None

    for f in files:
        if "lineage-" in f and ".zip" in f:
            lineage_zip_filename = f
        elif "boot.img" in f:
            boot_filename = f
        elif "recovery.img" in f:
            recovery_filename = f

    if boot_filename is None:
        raise FileNotFoundError("boot.img doesn't exist")
    if recovery_filename is None:
        raise FileNotFoundError("recovery.img doesn't exist")

    print("Boot into fastboot mode now")
    wait_until_string_appears(["fastboot", "devices"], "fastboot")
    print("Device is connected")
    run(f"fastboot flash boot tmp/{boot_filename}")
    run(f"fastboot flash recovery tmp/{recovery_filename}")
    print("Reboot to recovery mode and open adb sideload")
    wait_until_string_appears(["adb", "devices"], "\tsideload")

    run(f"adb sideload tmp/{lineage_zip_filename}")

    rm_tmp()


def lineage_with_microG_download(device_code):
    html = requests.get(f"https://download.lineage.microg.org/{device_code}/").text
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for i in soup.select("td>a"):
        links.append(i["href"])
    logging.debug(links)
    date = set()
    for i in links:
        a = re.search(r"\d{8}", i)
        if a != None:
            date.add(a.group())
        else:
            logging.debug(f"Can't match date in: {i}")
    maxdate = max(date)
    url = []
    for i in links:
        if (
            maxdate in i
            and ".sha256sum" not in i
            and "super_empty.img" not in i
            and "vbmeta.img" not in i
        ):
            url.append(f"https://download.lineage.microg.org/{device_code}/{i[2:]}")
    aria2c_download(" ".join(url), "tmp")


if __name__ == "__main__":
    lineage_download("polaris")
    # lineage_with_microG_download("polaris")
    lineage_flash()
    print("Done.")
