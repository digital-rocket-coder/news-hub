from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class FetchedArticle:
    title: str
    url: str
    description: str | None
    full_text: str | None
    published_at: datetime | None


class BaseConnector(ABC):
    """Abstract source connector. Implement to add new source types."""

    @abstractmethod
    async def fetch(self, url: str) -> list[FetchedArticle]:
        """Fetch articles from the given source URL."""
        ...
