# Standard Library
import logging
import time
from argparse import ArgumentParser
from dataclasses import dataclass
from typing import List, Optional

# Third Party
import requests
from discord import SyncWebhook, Embed
import yaml
from aoe import WorldsEdgeApiClient, ConfigPlayer, Match, Member


@dataclass
class Config:
    """The config file."""

    worldsedge_url: str
    discord_hook: str
    players: List[ConfigPlayer]


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


class MessageFormatter:
    """The discord message formatter."""

    def __init__(self, match: TeamMatch, clan_players: List[ConfigPlayer]) -> None:
        """Init actions."""
        # set required data
        self.teammates = self.extract_clan_teammates(match, clan_players)
        self.is_ranked = self.is_ranked_game(match.match.matchtype_id)
        self.is_training = self.is_training_game(match.teams, self.teammates, match.match.members)
        self.is_victory = self.clan_is_winner(self.teammates, self.is_training)

        self.teams = match.teams

        # format data
        self.color = self.set_color(self.is_training, self.is_victory)
        self.title = self.set_title(match.teams, match.match.mapname, self.is_ranked)
        self.insights_link = self.set_insights_link(match.match.insights_link)
        self.record_link = self.set_record_link(match.match.members)

    def generate_message(self) -> str:
        """Format the header message above the discord embed."""
        # ensure this is not an internal clan match for training
        if self.is_training:
            return "Match results."

        header = ""
        for n, m in enumerate(self.teammates):
            header += f"{m.profile.alias.capitalize()}"
            if n < len(self.teammates) - 2:
                header += ", "
            elif n < len(self.teammates) - 1:
                header += " and "

        # format title according to the result
        if self.is_victory is True:
            header += f" {'are' if len(self.teammates) > 1 else 'is'} victorious."
        else:
            header += f" {'have' if len(self.teammates) > 1 else 'has'} been defeated."

        return header

    def generate_embed(self) -> Embed:
        """Generates the embed to be sent by the discord client."""
        embed = Embed(color=self.color, title=self.title)
        if len(self.teams) != 2:
            self.format_multiline_desc(embed, self.teams)
        else:
            self.format_inline_desc(embed, self.teams)

        links = f"{self.insights_link}"
        if self.record_link is not None:
            links += f"\n{self.record_link}"
        embed.add_field(name='', value=links, inline=False)

        return embed

    def format_player_name(self, member: Member) -> str:
        """Builds the player name as a link with ELO ranking and country."""
        name = ""

        if member.profile.country:
            name += f":flag_{member.profile.country.lower()}: "
        else:
            name += ":globe_with_meridians: "
        alias = f"{member.profile.alias} ({member.oldrating})"
        name += f"[{alias}](https://www.aoe2insights.com/user/{member.profile.id}/)"
        if member.outcome > 0:
            name += " :crown:"
        return name

    def format_inline_desc(self, embed: Embed, teams: List[Team]) -> None:
        """Builds the message body for a game with only two teams."""
        for it, team in enumerate(teams):
            name = f"Team {it+1}"
            value = ""
            for ip, mb in enumerate(team.members):
                value += self.format_player_name(mb)
                if ip < len(team.members) - 1:
                    value += "\n"
            embed.add_field(name=name, value=value, inline=True)
            # this is just for spacing
            if it < len(teams) - 1:
                embed.add_field(name='', value='', inline=True)

    def format_multiline_desc(self, embed: Embed, teams: List[Team]) -> None:
        """Builds the message body for a game with more than two teams."""
        desc = ""

        for it, team in enumerate(teams):
            for ip, mb in enumerate(team.members):
                desc += self.format_player_name(mb)
                if ip < len(team.members) - 1:
                    desc += ", "
            if it < len(teams) - 1:
                desc += "\n**Versus**\n"

        embed.add_field(name=None, value=desc, inline=False)

    def set_insights_link(self, link: str) -> str:
        """Sets the link description to the AoE Insights statistics page."""
        return f"▸ **[Link to match insights]({link})**"

    def set_record_link(self, members: List[Member]) -> Optional[str]:
        """Sets the link description to download the record file."""
        logging.info("Looking for a valid record link")

        link = ""
        for mb in members:
            try:
                resp = requests.get(mb.replay_link)
                if resp.status_code == 200:
                    logging.info("Found a valid record link")
                    link = mb.replay_link
                    break
            except requests.exceptions.RequestException as e:
                logging.error(
                    f"couldn't validate the replay URL {mb.replay_link}, {e}"
                )
        if link:
            return f"▸ **[Download replay]({link})**"

    def set_title(self, teams: List[Team], mapname: str, is_ranked: bool) -> str:
        """Sets the title of the discord embed."""
        title = 'Ranked ' if is_ranked is True else ''

        for it, team in enumerate(teams):
            title += f"{len(team.members)}"
            if it < len(teams) - 1:
                title += " vs "

        title += f" on {mapname.split('.')[0].capitalize()}"
        return title

    def set_color(self, is_training: bool, is_victory: bool) -> int:
        """Sets the color of the discord embed."""
        if self.is_training is True:
            return 7506394 # blue
        if self.is_victory is True:
            return 5089895 # green
        return 10961731 # red

    def is_training_game(self, teams: List[Team], teammates: List[Member], members: List[Member]) -> bool:
        """Determines if the game was a training."""
        return len(teammates) == len(members) or len(teams) != 2

    def extract_clan_teammates(self, match: TeamMatch, clan_players: List[ConfigPlayer]) -> List[Member]:
        """Returns the members of the clan as a list."""
        # prefix with result only when 2 teams are playing
        teammates: List[Member] = []
        if len(match.teams) == 2:
            for mb in match.match.members:
                for clan_player in clan_players:
                    if mb.profile.id == clan_player.profileId:
                        teammates.append(mb)
        return teammates

    def clan_is_winner(self, teammates: List[Member], is_training: bool) -> bool:
        """Determines if the clan has won the game."""
        if is_training is True:
            logging.info("this was an internal match")
            return False

        # is the clan successful ?
        winners = [teammate for teammate in teammates if teammate.outcome > 0]
        if len(winners) > 0:
            logging.info("the clan is victorious")
            return True

        logging.info("the clan has been defeated")
        return False

    def is_ranked_game(self, matchtype_id: int) -> bool:
        """Determines if the game was ranked."""
        Gametypes = {
            0: 'Unranked',
            2: 'Ranked Deathmatch',
            6: 'Ranked Random Map 1v1',
            7: 'Ranked Random Map 2v2',
            8: 'Ranked Random Map 3v3',
            9: 'Ranked Random Map 4v4',
            26: 'Ranked Empire Wars 1v1',
            27: 'Ranked Empire Wars 2v2',
            28: 'Ranked Empire Wars 3v3',
            29: 'Ranked Empire Wars 4v4',
            120: 'Ranked Return of Rome 1v1',
            121: 'Ranked Return of Rome Team',
        }

        try:
            return 'ranked' in Gametypes[matchtype_id].lower()
        except KeyError:
            return False


class Engine:
    """The notifier engine."""

    def __init__(self, cli: WorldsEdgeApiClient, webhook: SyncWebhook, pls: List[ConfigPlayer]) -> None:
        """Inits Actions."""
        self.cli = cli
        self.webhook = webhook
        self.players = pls

    def run(self) -> None:
        """Starts the infinite loop."""
        prev = self.get_lastmatches()
        if prev is None:
            logging.error("could't initialize matches")
            return

        logging.info("recent matches initialized")
        while True:
            time.sleep(50)
            new = self.get_lastmatches()
            if new is None:
                logging.error("could't refresh matches")
                continue

            self.check_results(prev, new)
            prev = new
            logging.info("matches refreshed")

    def check_results(self, prev: List[TeamMatch], new: List[TeamMatch]) -> None:
        """Post results for new matches."""
        for n in new:
            found = [p for p in prev if p.match.id == n.match.id]
            if not found:
                logging.info(f"new finished match: {n.versus_str()}")
                formatter = MessageFormatter(match=n, clan_players=self.players)
                message = formatter.generate_message()
                embed = formatter.generate_embed()
                self.webhook.send(content=message, embed=embed)

    def get_lastmatches(self) -> Optional[List[TeamMatch]]:
            """Get last matches and removes ongoing matches from the list."""
            team_matches = []

            matches = self.cli.get_lastmatches(self.players)

            for match in matches:
                teams = self.set_teams(match.members)
                team_matches.append(TeamMatch(match=match, teams=teams))

            return team_matches

    def set_teams(self, members: List[Member]) -> List[Team]:
        teams: list[Team] = []

        for member in members:
            # find member's team
            found = False
            for team in teams:
                if member.teamid > -1 and team.number == member.teamid:
                    team.members.append(member)
                    found = True

            # create team otherwise
            if found is False:
                teams.append(Team(
                    number=member.teamid,
                    members=[member]
                ))

        sorted_teams = sorted(teams, key=lambda team: team.number)
        return sorted_teams

def main(config_file: str) -> None:
    logging.info(f"loading config file {config_file}")

    try:
        with open(config_file, "r") as stream:
            data = yaml.safe_load(stream)
            config = Config(
                worldsedge_url=data["worldsedge_url"],
                discord_hook=data["discord_hook"],
                players=[
                    ConfigPlayer(
                        name=pl["name"],
                        steamId=pl["steamId"],
                        profileId=pl["profileId"],
                    )
                    for pl in data["players"]
                ],
            )

            cli = WorldsEdgeApiClient(url=config.worldsedge_url)
            webhook = SyncWebhook.from_url(config.discord_hook)
            engine = Engine(cli, webhook, config.players)

            # run the infinite loop
            logging.info("starting AoE Engine...")
            engine.run()
            logging.info("exiting...")

    except Exception as exc:
        logging.error(exc)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # parse arguments
    parser = ArgumentParser()
    parser.add_argument("--config-file", type=str, help="Path to config file.")
    args = parser.parse_args()

    # start
    main(args.config_file)
