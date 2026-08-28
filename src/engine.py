# Standard Library
import logging
import time
from typing import List, Optional

# Third Party
from discord import SyncWebhook

from aoe import WorldsEdgeApiClient
from link_resolver import LinkResolver
from match_classifier import classify, set_teams
from message_formatter import MatchPresentation, MessageFormatter
from models import ConfigPlayer, TeamMatch, Translations

logger = logging.getLogger(__name__)


class Engine:
    """The notifier engine."""

    def __init__(
        self,
        cli: WorldsEdgeApiClient,
        webhook: SyncWebhook,
        link_resolver: LinkResolver,
        players: List[ConfigPlayer],
        translations: Translations,
    ) -> None:
        """Inits Actions."""
        self.cli = cli
        self.webhook = webhook
        self.link_resolver = link_resolver
        self.players = players
        self.text = translations

    def run(self) -> None:
        """Starts the infinite loop."""
        prev = self.get_lastmatches()
        if prev is None:
            logger.error("couldn't initialize matches")
            return

        logger.info("recent matches initialized")
        while True:
            time.sleep(50)
            new = self.get_lastmatches()
            if new is None:
                logger.error("couldn't refresh matches")
                continue

            self.check_results(prev, new)
            prev = new
            logger.info("matches refreshed")

    def check_results(self, prev: List[TeamMatch], new: List[TeamMatch]) -> None:
        """Post results for new matches."""
        for n in new:
            found = [p for p in prev if p.match.id == n.match.id]
            if found:
                continue

            logger.info(f"new finished match: {n.versus_str()}")
            try:
                self._notify(n)
            except Exception:
                logger.exception(f"failed to process match {n.match.id}")

    def _notify(self, team_match: TeamMatch) -> None:
        """Classifies, resolves links, formats and sends one match to Discord."""
        classification = classify(team_match, self.players)
        insights_link = self.link_resolver.first_reachable([team_match.match.insights_link])
        record_link = self.link_resolver.first_reachable(
            [mb.replay_link for mb in team_match.match.members]
        )

        presentation = MatchPresentation(
            teams=team_match.teams,
            teammates=classification.teammates,
            mapname=team_match.match.mapname,
            is_ranked=classification.is_ranked,
            is_training=classification.is_training,
            is_victory=classification.is_victory,
            insights_link=insights_link,
            record_link=record_link,
        )

        formatter = MessageFormatter(presentation, self.text)
        message = formatter.generate_message()
        embed = formatter.generate_embed()
        self.webhook.send(content=message, embed=embed)

    def get_lastmatches(self) -> Optional[List[TeamMatch]]:
        """Get last matches and removes ongoing matches from the list."""
        team_matches = []

        matches = self.cli.get_lastmatches(self.players)
        if matches is None:
            return None

        for match in matches:
            teams = set_teams(match.members)
            team_matches.append(TeamMatch(match=match, teams=teams))

        return team_matches
