import logging
import os
import random
import secrets

from src.screenshots import retrieveCoverArt


def test_retrieveCoverArt_wikipedia() -> None:
    logging.info("generate random seed")
    seed = random.randint(
        1,
        256,
    )

    test_bin_dir_path = "bin/tests"
    os.makedirs(
        test_bin_dir_path,
        exist_ok=True,
    )

    test_bin_path = f"{test_bin_dir_path}/{secrets.randbelow(seed)}.png"

    wikipedia_page_url = "https://en.wikipedia.org/wiki/The_Dawn_of_the_Black_Hearts"

    retrieveCoverArt(
        url=wikipedia_page_url,
        output_filename=test_bin_path,
        is_verbose=True,
    )

    try:
        with open(file=test_bin_path, mode="rb") as file:
            file_contents: bytes = file.read()

            assert file_contents is not None

        os.remove(path=test_bin_path)
    except Exception as e:
        raise e
