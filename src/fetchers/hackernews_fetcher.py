"""Fetch top stories from HackerNews."""

import asyncio
from typing import List, Optional

import aiohttp

from src.fetchers.base_fetcher import BaseFetcher
from src.models.article import Article
from src.storage.markdown_storage import MarkdownStorage
from src.utils.rate_limiter import RateLimiter


class HackerNewsFetcher(BaseFetcher):
    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    def __init__(self, transformer=None, storage=None):
        self.transformer = transformer
        self.storage = storage or MarkdownStorage()
        self.rate_limiter = RateLimiter(max_concurrent=10)

    async def fetch_articles(self) -> List[Article]:
        """Fetch from HackerNews API."""
        url = "https://hacker-news.firebaseio.com/v0/topstories.json"

        async with aiohttp.ClientSession() as session:
            # Get top story IDs
            async with session.get(url) as response:
                story_ids = await response.json()

            # Fetch first 30 stories
            stories = []
            for story_id in story_ids[:30]:
                item_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                async with session.get(item_url) as response:
                    item = await response.json()
                    if item:
                        stories.append(item)

            # Transform using injected transformer
            return self.transformer.transform_hackernews(stories)

    def get_source_name(self) -> str:
        """Return source name."""
        return "hackernews"

    async def fetch(self, limit: int = 30) -> List[Article]:
        print(f"📰 Fetching {limit} stories from HackerNews...")

        story_ids = await self._fetch_top_story_ids()

        if not story_ids:
            return []

        raw_items = await self._fetch_stories(story_ids[:limit])

        if self.transformer:
            articles = self.transformer.transform_hackernews(raw_items)
        else:
            articles = raw_items

        print(f"✅ Fetched {len(articles)} HackerNews stories")

        return articles

    async def fetch_and_save(self, limit: int = 30) -> List[Article]:
        articles = await self.fetch(limit)

        if articles:
            self.storage.save(articles, "hackernews_articles.md")

        return articles

    async def _fetch_top_story_ids(self) -> List[int]:
        url = f"{self.BASE_URL}/topstories.json"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    return await response.json()

        except Exception as e:
            print(f"⚠️ Failed to fetch story ids: {e}")
            return []

    async def _fetch_stories(self, story_ids: List[int]) -> List[dict]:
        async with aiohttp.ClientSession() as session:
            tasks = [self._fetch_story(session, story_id) for story_id in story_ids]

            results = await asyncio.gather(*tasks)

            return [r for r in results if r is not None]

    async def _fetch_story(
        self, session: aiohttp.ClientSession, story_id: int
    ) -> Optional[dict]:
        url = f"{self.BASE_URL}/item/{story_id}.json"

        try:
            async with self.rate_limiter:
                async with session.get(url) as response:
                    response.raise_for_status()
                    data = await response.json()

                    if not data:
                        return None

                    if data.get("type") != "story":
                        return None

                    if not data.get("url"):
                        return None

                    return data

        except Exception as e:
            print(f"⚠️ Failed story {story_id}: {e}")
            return None
