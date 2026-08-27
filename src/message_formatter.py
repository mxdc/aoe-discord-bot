# Standard Library
import logging
from dataclasses import dataclass
from typing import List, Optional

# Third Party
from discord import Embed

from models import Member, Team, Translations

logger = logging.getLogger(__name__)


@dataclass
class MatchPresentation:
    """Everything MessageFormatter needs to render a match, already computed."""

    teams: List[Team]
    teammates: List[Member]
    mapname: str
    is_ranked: bool
    is_training: bool
    is_victory: bool
    insights_link: Optional[str] = None
    record_link: Optional[str] = None


class MessageFormatter:
    """The discord message formatter."""

    def __init__(self, match: MatchPresentation, translations: Translations) -> None:
        """Init actions."""
        self.match = match
        self.text = translations
        self.color = self.set_color(match.is_training, match.is_victory)
        self.title = self.set_title(match.teams, match.mapname, match.is_ranked)

    def generate_message(self) -> str:
        """Format the header message above the discord embed."""
        # ensure this is not an internal clan match for training
        if self.match.is_training:
            return self.text.match_results

        teammates = self.match.teammates
        header = ""
        for n, m in enumerate(teammates):
            header += f"{m.profile.alias.capitalize()}"
            if n < len(teammates) - 2:
                header += self.text.players_separator
            elif n < len(teammates) - 1:
                header += self.text.players_last_separator

        # format title according to the result
        if self.match.is_victory is True:
            if len(teammates) > 1:
                return self.text.victory_plural.format(players=header)
            return self.text.victory_singular.format(player=header)
        else:
            if len(teammates) > 1:
                return self.text.defeat_plural.format(players=header)
            return self.text.defeat_singular.format(player=header)

    def generate_embed(self) -> Embed:
        """Generates the embed to be sent by the discord client."""
        teams = self.match.teams
        embed = Embed(color=self.color, title=self.title)
        if len(teams) != 2:
            self.format_multiline_desc(embed, teams)
        else:
            self.format_inline_desc(embed, teams)

        links = []
        if self.match.insights_link is not None:
            links.append(self.text.view_match_details.format(link=self.match.insights_link))
        if self.match.record_link is not None:
            links.append(self.text.download_replay.format(link=self.match.record_link))
        if len(links) > 0:
            embed.add_field(name='', value="\n".join(links), inline=False)

        return embed

    def format_player_name(self, member: Member) -> str:
        """Builds the player name as a link with ELO ranking and country."""
        name = ""

        if member.profile.country:
            name += self.text.emoji_flag.format(country=member.profile.country.lower())
        else:
            name += self.text.emoji_globe
        name += " "
        alias = f"{member.profile.alias} ({member.oldrating})"
        name += f"[{alias}](https://www.aoe2insights.com/user/{member.profile.id}/)"
        if member.outcome > 0:
            name += " " + self.text.emoji_crown
        return name

    def format_inline_desc(self, embed: Embed, teams: List[Team]) -> None:
        """Builds the message body for a game with only two teams."""
        if len(teams) != 2:
            logger.error("format_inline_desc should only be used for 2 teams")
            return

        team1 = teams[0]
        team2 = teams[1]
        # 1v1 case, format as "Player1 vs Player2"
        if len(team1.members) == 1 and len(team2.members) == 1:
            player1 = self.format_player_name(team1.members[0])
            player2 = self.format_player_name(team2.members[0])
            vs_text = f"*{self.text.versus_short}*"
            value = f"**{player1}**  {vs_text}  **{player2}**"
            embed.add_field(name='', value=value, inline=False)
            return

        # format teams as columns
        for it, team in enumerate(teams):
            value = self.text.team_label.format(number=it+1) + "\n"
            for ip, mb in enumerate(team.members):
                value += f"**{self.format_player_name(mb)}**"
                if ip < len(team.members) - 1:
                    value += "\n"
            embed.add_field(name='', value=value, inline=True)
            # this is just for spacing
            if it < len(teams) - 1:
                embed.add_field(name='', value='', inline=True)

    def format_multiline_desc(self, embed: Embed, teams: List[Team]) -> None:
        """Builds the message body for a game with more than two teams."""
        desc = ""

        for it, team in enumerate(teams):
            for ip, mb in enumerate(team.members):
                desc += f"**{self.format_player_name(mb)}**"
                if ip < len(team.members) - 1:
                    desc += self.text.players_separator
            if it < len(teams) - 1:
                desc += "\n" + self.text.versus_long + "\n"

        embed.add_field(name='', value=desc, inline=False)

    def set_title(self, teams: List[Team], mapname: str, is_ranked: bool) -> str:
        """Sets the title of the discord embed."""
        title = self.text.ranked if is_ranked is True else self.text.unranked

        for it, team in enumerate(teams):
            title += f"{len(team.members)}"
            if it < len(teams) - 1:
                title += f" {self.text.versus_short} "

        # title += f" on {mapname.split('.')[0].capitalize()}"
        return title

    def set_color(self, is_training: bool, is_victory: bool) -> int:
        """Sets the color of the discord embed."""
        if is_training is True:
            return 7506394  # blue
        if is_victory is True:
            return 3066993  # green
        return 15158332  # red
