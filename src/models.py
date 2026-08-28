# Standard Library
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ConfigPlayer:
    """Represents the player in the config file."""

    name: Optional[str] = None
    profileId: Optional[int] = None
    steamId: Optional[int] = None


@dataclass
class Profile:
    """Represents the profile."""

    id: int
    name: str
    alias: str
    personal_statgroup_id: int
    xp: int
    country: str


@dataclass
class Member:
    """Represents the player in a match."""

    profile: Optional[Profile]
    civilization_id: int
    newrating: int
    oldrating: int
    outcome: int
    teamid: int
    replay_link: str


@dataclass
class Match:
    """Represents the match."""

    id: int
    mapname: str
    matchtype_id: int
    description: str
    startgametime: int
    completiontime: int
    insights_link: str
    members: List[Member]


@dataclass
class PlayerMatches:
    """Private class that combines the player with his recent matches."""

    matches: List[Match]
    steam_id: str


@dataclass
class Config:
    """The config file."""

    worldsedge_url: str
    discord_hook: str
    players: List[ConfigPlayer]


@dataclass
class Translations:
    """Typed translations for Discord messages."""

    # Match result messages
    match_results: str

    # Victory/Defeat messages
    victory_plural: str
    victory_singular: str
    defeat_plural: str
    defeat_singular: str

    # Player list formatting
    players_separator: str
    players_last_separator: str

    # Match details
    versus_short: str
    versus_long: str
    team_label: str

    # Match type labels
    ranked: str
    unranked: str

    # Links
    view_match_details: str
    download_replay: str

    # Emojis
    emoji_crown: str
    emoji_flag: str
    emoji_globe: str


@dataclass
class Team:
    """Class representing a team."""

    members: List[Member]
    number: int


@dataclass
class TeamMatch:
    """Class representing a match with players sorted by team."""

    match: Match
    teams: List[Team]

    def versus_str(self) -> str:
        """Return list of players as string."""
        s = ""
        for i, team in enumerate(self.teams):
            for ip, mb in enumerate(team.members):
                s += mb.profile.alias
                if ip < len(team.members) - 1:
                    s += ", "
            if i < len(self.teams) - 1:
                s += " vs "
        return s
