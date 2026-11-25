"""Main entry point for news fetcher."""

import asyncio
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.fetchers.github_trending_fetcher import GitHubTrendingFetcher
from src.fetchers.hackernews_fetcher import HackerNewsFetcher
from src.orchestrator import FetchOrchestrator
from src.storage.markdown_storage import MarkdownStorage
from src.transformers.article_transformer import ArticleTransformer


async def main():
    """Main entry point with dependency injection."""

    # Create dependencies
    transformer = ArticleTransformer()
    storage = MarkdownStorage("data/articles")

    # Create fetchers
    fetchers = [
        HackerNewsFetcher(transformer, storage),
        GitHubTrendingFetcher(transformer, storage),
    ]

    # Inject dependencies into orchestrator
    orchestrator = FetchOrchestrator(
        transformer=transformer,
        storage=storage,
        fetchers=fetchers,
    )

    # Run
    articles = await orchestrator.fetch_all()
    print(f"✅ Fetched {len(articles)} articles total")


if __name__ == "__main__":
    asyncio.run(main())
