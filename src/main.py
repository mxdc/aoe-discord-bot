# Standard Library
import logging
from argparse import ArgumentParser

# Third Party
import requests
from discord import SyncWebhook

from aoe import WorldsEdgeApiClient
from config import load_config, load_translations
from engine import Engine
from link_resolver import LinkResolver

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 10


def main(config_file: str, translations_file: str) -> None:
    logger.info(f"loading config file {config_file}")
    config = load_config(config_file)

    logger.info(f"loading translations file {translations_file}")
    translations = load_translations(translations_file)

    session = requests.Session()
    cli = WorldsEdgeApiClient(url=config.worldsedge_url, session=session, timeout=REQUEST_TIMEOUT)
    link_resolver = LinkResolver(session=session, timeout=REQUEST_TIMEOUT)
    webhook = SyncWebhook.from_url(config.discord_hook)
    engine = Engine(cli, webhook, link_resolver, config.players, translations)

    # run the infinite loop
    logger.info("starting AoE Engine...")
    engine.run()
    logger.info("exiting...")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # parse arguments
    parser = ArgumentParser()
    parser.add_argument("--config-file", type=str, help="Path to config file.")
    parser.add_argument("--translations-file", type=str, help="Path to translations file.")
    args = parser.parse_args()

    # start
    main(args.config_file, args.translations_file)
