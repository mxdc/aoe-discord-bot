# Standard Library
import logging
from typing import List, Optional

# Third Party
import requests

from models import ConfigPlayer, Match, Member, PlayerMatches, Profile

logger = logging.getLogger(__name__)


class WorldsEdgeApiClient:
    """The HTTP client for World's Edge."""

    def __init__(self, url: str, session: requests.Session, timeout: float = 10) -> None:
        self.url = url
        self.session = session
        self.timeout = timeout

    def get_matches(self, players: List[ConfigPlayer]) -> Optional[List[PlayerMatches]]:
        """Performs the HTTP requests."""
        pms: List[PlayerMatches] = []

        for pl in players:
            logger.info(f"getting {pl.name} (id: {pl.steamId}) matches...")

            resp = self.session.get(
                f'{self.url}/community/leaderboard/getRecentMatchHistory?title=age2&profile_names=[%22/steam/{pl.steamId}%22]',
                timeout=self.timeout,
            )
            if resp.status_code != 200:
                logger.error(f"HTTP request error with status: {resp.status_code}")
                return None

            data = resp.json()
            matches = data['matchHistoryStats']
            profiles = [
                Profile(
                    id=profile['profile_id'],
                    name=profile['name'],
                    alias=profile['alias'],
                    personal_statgroup_id=profile['personal_statgroup_id'],
                    xp=profile['xp'],
                    country=profile['country'],
                )
                for profile in data['profiles']
            ]

            parsedMatches = []
            for match in matches:
                matchMembers = [
                    Member(
                        profile=self.find_member_profile(profiles, member['profile_id']),
                        civilization_id=member['civilization_id'],
                        teamid=member['teamid'],
                        outcome=member['outcome'],
                        oldrating=member['oldrating'],
                        newrating=member['newrating'],
                        replay_link=self.get_replay(match['id'], member['profile_id']),
                    )
                    for member in match['matchhistorymember']
                ]

                game_id = match['id']
                parsedMatch = Match(
                    id=game_id,
                    mapname=match['mapname'],
                    matchtype_id=match['matchtype_id'],
                    description=match['description'],
                    startgametime=match['startgametime'],
                    completiontime=match['completiontime'],
                    insights_link=f'https://www.aoe2insights.com/match/{game_id}/',
                    members=matchMembers,
                )
                parsedMatches.append(parsedMatch)

            pms.append(PlayerMatches(steam_id=pl.steamId, matches=parsedMatches))

        logger.info(f"found matches for {len(pms)}/{len(players)} players")
        return pms

    def get_lastmatches(self, players: List[ConfigPlayer]) -> Optional[List[Match]]:
        """Gathers last finished matchs for each player."""
        matches: List[Match] = []
        dedups: List[Match] = []

        pms = self.get_matches(players)
        if pms is None:
            return None

        # keep last 5 most recent matches for each player
        for pm in pms:
            sorted_matches = sorted(pm.matches, key=lambda match: match.startgametime, reverse=True)
            matches += sorted_matches[:5]

        # remove duplicates
        for match in matches:
            if match.id in [d.id for d in dedups]:
                continue
            dedups.append(match)

        return dedups

    def find_member_profile(self, profiles: List[Profile], profile_id: int) -> Optional[Profile]:
        """Finds the profile by ID."""
        filtered_profiles = [profile for profile in profiles if profile.id == profile_id]

        if len(filtered_profiles) == 0: return None

        return filtered_profiles[0]

    def get_replay(self, match_id: int, profile_id: int) -> str:
        """Generates the replay link."""
        record_link = f'https://aoe.ms/replay/?gameId={match_id}&profileId={profile_id}'

        return record_link
