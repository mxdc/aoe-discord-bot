# Standard Library
import logging
from dataclasses import dataclass
from typing import List

from models import ConfigPlayer, Member, Team, TeamMatch

logger = logging.getLogger(__name__)


@dataclass
class MatchClassification:
    """The result of classifying a match: who's tracked, and how it ended."""

    teammates: List[Member]
    is_ranked: bool
    is_training: bool
    is_victory: bool


def classify(team_match: TeamMatch, clan_players: List[ConfigPlayer]) -> MatchClassification:
    """Classifies a match: tracked teammates, ranked/training/victory status."""
    teammates = extract_clan_teammates(team_match, clan_players)
    is_ranked = is_ranked_game(team_match.match.matchtype_id)
    is_training = is_training_game(team_match.teams, teammates, team_match.match.members)
    is_victory = clan_is_winner(teammates, is_training)

    return MatchClassification(
        teammates=teammates,
        is_ranked=is_ranked,
        is_training=is_training,
        is_victory=is_victory,
    )


def is_ranked_game(matchtype_id: int) -> bool:
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


def is_training_game(teams: List[Team], teammates: List[Member], members: List[Member]) -> bool:
    """Determines if the game was a training."""
    return len(teammates) == len(members) or len(teams) != 2


def extract_clan_teammates(match: TeamMatch, clan_players: List[ConfigPlayer]) -> List[Member]:
    """Returns the members of the clan as a list."""
    # prefix with result only when 2 teams are playing
    teammates: List[Member] = []
    if len(match.teams) == 2:
        for mb in match.match.members:
            for clan_player in clan_players:
                if mb.profile.id == clan_player.profileId:
                    teammates.append(mb)
    return teammates


def clan_is_winner(teammates: List[Member], is_training: bool) -> bool:
    """Determines if the clan has won the game."""
    if is_training is True:
        logger.info("this was an internal match")
        return False

    # is the clan successful ?
    winners = [teammate for teammate in teammates if teammate.outcome > 0]
    if len(winners) > 0:
        logger.info("the clan is victorious")
        return True

    logger.info("the clan has been defeated")
    return False


def set_teams(members: List[Member]) -> List[Team]:
    """Groups match members into teams, sorted by team number."""
    teams: List[Team] = []

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
