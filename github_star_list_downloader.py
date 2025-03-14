import os
from bs4 import BeautifulSoup
import requests
import logging
from typing_extensions import Annotated
import typer


logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def run(command):
    return os.system(command)


def aria2c_download(urls, directory):
    if run(f"aria2c -c -s 8 -x 8 -k 1M -j 1 -Z --dir {directory} {urls}") == 0:
        print(f"Downloaded {urls} successfully")
    else:
        raise Exception(f"Failed to download {urls}")


def parse_star_list(url):
    html = requests.get(url).text
    soup = BeautifulSoup(html, "html.parser")
    href = soup.select("#user-list-repositories .d-inline-block a")
    links = []
    for i in href:
        links.append(f"https://api.github.com/repos{i['href']}/releases")
    return links


def parse_releases_api(url):
    latest_res = requests.get(url).json()[0]["assets"]
    if len(latest_res) == 1:
        logging.debug(f"res len == 1: {latest_res[0]['name']}")
        return latest_res[0]["browser_download_url"]
    else:
        for i in latest_res:
            name = i["name"]
            if "arm64" in name and name.endswith(".apk"):
                logging.debug(f"has arm64: {name}")
                return i["browser_download_url"]
            elif "release" in name:
                logging.debug(f"has release: {name}")
                return i["browser_download_url"]
            elif name.endswith(".apk"):
                logging.debug(f"endswith .apk: {name}")
                return i["browser_download_url"]
    raise Exception(f"Can't parse {url}")


def main(
    star_list_url: Annotated[
        str, typer.Argument(help="Like https://github.com/stars/xxx/lists/xxxxxxx")
    ],
    dir: Annotated[
        str, typer.Option(help="The directory to store the downloaded file.")
    ] = "./",
):
    links = parse_star_list(star_list_url)
    urls = []
    for u in links:
        urls.append(parse_releases_api(u))
    aria2c_download(" ".join(urls), dir)


if __name__ == "__main__":
    typer.run(main)
