# Standard Library
import logging
from typing import List, Optional

# Third Party
import requests

logger = logging.getLogger(__name__)


class LinkResolver:
    """Validates that a URL is reachable before it's shared in a Discord message."""

    def __init__(self, session: requests.Session, timeout: float = 10) -> None:
        self.session = session
        self.timeout = timeout

    def first_reachable(self, urls: List[str]) -> Optional[str]:
        """Returns the first URL in the list that responds with HTTP 200, or None."""
        for url in urls:
            if not url:
                continue
            try:
                resp = self.session.get(url, timeout=self.timeout)
                if resp.status_code == 200:
                    return url
            except requests.exceptions.RequestException as exc:
                logger.debug(f"link check failed for {url}: {exc}")

        return None
