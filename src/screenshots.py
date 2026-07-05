"""
jukebox

create theme screenshot
"""

import logging
from collections.abc import Mapping

import regex
import requests
from bs4 import BeautifulSoup


# TODO: add verbosity
def retrieveCoverArt(
    url: str | None = None,
    output_filename: str | None = None,
    is_verbose: bool = False,
) -> None:
    if url is None:
        if is_verbose:
            logging.info(f"url: {url}, please provide a url")

        return

    headers: Mapping[str, str | bytes] = {
        "User-Agent": "jukebox/0.0 (https://github.com/nooneknowspeter/jukebox/; nooneknows)",
    }

    if is_verbose:
        logging.info(f"set headers: {headers}")

    if is_verbose:
        logging.info(f"get request url: {url}")

    response: requests.Response = requests.get(
        url=url,
        headers=headers,
    )

    if is_verbose:
        logging.info(f"response: {response}")

    response_body = response.content

    soup = BeautifulSoup(
        markup=response_body,
        features="html.parser",
    )

    # TODO: strat pattern
    # find url source kind; spotify, wikipedia, direct image url

    cover_art_uri: str = ""

    if regex.search("wikipedia", url) is not None:
        if is_verbose:
            logging.info("source: wikipedia")

        cover_art_uri = f"https:{str(soup.find_all('img')[3]['src'])}"

    if regex.search("spotify", url) is not None:
        if is_verbose:
            logging.info("soruce: spotify")

        cover_art_uri = str(soup.find_all("img")[0]["src"])

    if is_verbose:
        logging.info(f"get cover image content: {cover_art_uri}")

    cover_art_bin: bytes = requests.get(
        url=cover_art_uri,
        headers=headers,
    ).content

    if cover_art_uri:
        with open(file=output_filename, mode="wb") as file:
            try:
                if is_verbose:
                    logging.info(f"saving to {output_filename}")

                _ = file.write(cover_art_bin)
            except Exception as e:
                if is_verbose:
                    logging.fatal(f"{e}")

                raise e


# TODO: get theme manifest

# TODO: read and marshal

# TODO: get cover art

# TODO: create color cards

# TODO: merge with pil

# TODO: output screenshots


def main() -> None:
    pass


if __name__ == "__main__":
    main()
