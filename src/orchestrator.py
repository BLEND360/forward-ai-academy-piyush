"""Orchestrate multiple news fetchers."""

import asyncio
from typing import List, Optional

from src.fetchers.base_fetcher import BaseFetcher
from src.fetchers.hackernews_fetcher import HackerNewsFetcher
from src.fetchers.rss_fetcher import RSSFetcher
from src.models.article import Article
from src.storage.base_storage import ArticleStorage
from src.storage.markdown_storage import MarkdownStorage
from src.transformers.article_transformer import ArticleTransformer


class FetchOrchestrator:
    """
    Orchestrates multiple fetchers.

    Follows Dependency Inversion Principle:
    - Depends on abstractions (BaseFetcher, ArticleStorage)
    - Dependencies injected via constructor
    """

    def __init__(
        self,
        transformer: Optional[ArticleTransformer] = None,
        storage: Optional[ArticleStorage] = None,
        fetchers: Optional[List[BaseFetcher]] = None,
    ):
        """
        Initialize with injected dependencies.

        Args:
            fetchers: List of fetcher instances
            storage: Storage implementation
            transformer: Transformer instance
        """
        self.transformer = transformer or ArticleTransformer()
        self.storage = storage or MarkdownStorage("data/articles")
        self.fetchers = fetchers or []

    def _build_default_fetchers(self) -> List[BaseFetcher]:
        """Create the default set of fetchers."""
        return [
            HackerNewsFetcher(self.transformer, self.storage),
            RSSFetcher("https://hnrss.org/frontpage", self.transformer, self.storage),
        ]

    async def fetch_all(self) -> List[Article]:
        """Fetch from all sources."""
        if not self.fetchers:
            self.fetchers = self._build_default_fetchers()

        all_articles = []

        for fetcher in self.fetchers:
            articles = await fetcher.fetch_and_save()
            all_articles.extend(articles)

        return all_articles


async def main():
    """Manual test entrypoint for orchestrator module."""
    transformer = ArticleTransformer()
    storage = MarkdownStorage()
    orchestrator = FetchOrchestrator(transformer=transformer, storage=storage)
    articles = await orchestrator.fetch_all()

    print("\n📊 Sample articles:")
    for article in articles[:5]:
        print(f"  [{article.source}] {article.title[:60]}...")


if __name__ == "__main__":
    asyncio.run(main())
