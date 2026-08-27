# Third Party
import yaml

from models import Config, ConfigPlayer, Translations


def load_config(path: str) -> Config:
    """Loads the config file. Raises on a missing file, bad YAML, or a missing key."""
    with open(path, "r") as stream:
        data = yaml.safe_load(stream)

    return Config(
        worldsedge_url=data["worldsedge_url"],
        discord_hook=data["discord_hook"],
        players=[
            ConfigPlayer(
                name=pl["name"],
                steamId=int(pl["steamId"]),
                profileId=int(pl["profileId"]),
            )
            for pl in data["players"]
        ],
    )


def load_translations(path: str) -> Translations:
    """Loads the translations file. Raises on a missing file or a missing key."""
    with open(path, "r") as stream:
        data = yaml.safe_load(stream)

    return Translations(**data)
