import json
import re
from pathlib import Path
from typing import Any, Dict, List

from src.agents.base_agent import BaseAgent


class NewsFilterAgent(BaseAgent):
    """Filter articles for AI/ML relevance."""

    def __init__(self):
        super().__init__()
        self.relevance_threshold = 6  # Out of 10

    async def _load_context(self, input_path: str) -> Dict[str, Any]:
        """
        Load articles from markdown file.

        Args:
            input_path: Path to markdown file with articles

        Returns:
            Dict with articles list
        """
        print(f"📖 Loading articles from {input_path}")

        content = Path(input_path).read_text(encoding="utf-8")
        articles = self._parse_markdown(content)

        print(f"   Found {len(articles)} articles")
        return {"articles": articles}

    def _parse_markdown(self, content: str) -> List[Dict[str, str]]:
        """Parse markdown content to extract articles."""
        articles: List[Dict[str, str]] = []

        sections = content.split("---")

        for section in sections:
            if "##" not in section:
                continue

            title_match = re.search(r"## (.+)", section)
            if not title_match:
                continue

            title = title_match.group(1).strip()

            url_match = re.search(r"\*\*URL:\*\* (.+)", section)
            url = url_match.group(1).strip() if url_match else ""

            lines = [
                l for l in section.split("\n") if l.strip() and not l.startswith("**")
            ]
            summary = lines[-1] if lines else ""

            articles.append(
                {
                    "title": title,
                    "url": url,
                    "summary": summary,
                }
            )

        return articles

    async def _process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter articles using LLM.

        Args:
            context: Dict with articles

        Returns:
            Dict with filtered articles and metadata
        """
        articles = context["articles"]
        print(f"🔍 Filtering {len(articles)} articles...")

        filtered: List[Dict[str, Any]] = []

        for i, article in enumerate(articles):
            print(f"   [{i + 1}/{len(articles)}] {article['title'][:50]}...")

            judgment = await self._judge_relevance(article)

            if (
                judgment["relevant"]
                and judgment["relevance_score"] >= self.relevance_threshold
            ):
                filtered.append(
                    {
                        **article,
                        "relevance_score": judgment["relevance_score"],
                        "reasoning": judgment["reasoning"],
                        "key_topics": judgment.get("key_topics", []),
                    }
                )
                print(f"      ✅ Relevant (score: {judgment['relevance_score']})")
            else:
                print(f"      ❌ Not relevant (score: {judgment['relevance_score']})")

        print(f"\n📊 Filtered: {len(filtered)}/{len(articles)} articles")

        return {
            "filtered_articles": filtered,
            "total_input": len(articles),
            "total_output": len(filtered),
        }

    async def _judge_relevance(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use LLM to judge article relevance.

        Args:
            article: Article dict with title, url, summary

        Returns:
            Dict with relevant, relevance_score, reasoning
        """
        prompt = f"""You are an expert AI/ML news analyst. Judge if this article is relevant to AI/ML.
Article: Title: {article['title']} Summary: {article['summary']}

Relevant topics include: Machine Learning, LLMs, Neural Networks, Computer Vision, NLP, AI Research, AI Applications, Deep Learning, Transformers, GPT, Stable Diffusion, AI Ethics, AI Safety

Output ONLY valid JSON with this exact format: {{ "relevant": true or false, "relevance_score": 1-10, "reasoning": "brief explanation", "key_topics": ["topic1", "topic2"] }}

Examples: - "GPT-4 Released" -> {{"relevant": true, "relevance_score": 10, "reasoning": "Major LLM release", "key_topics": ["LLM", "GPT"]}} - "New JavaScript Framework" -> {{"relevant": false, "relevance_score": 1, "reasoning": "Web dev, not AI", "key_topics": []}}

Your JSON response:"""

        try:
            response = await self._call_llm(prompt)

            # LLM might wrap JSON in markdown code fences.
            json_text = response
            if "```json" in response:
                json_text = response.split("```json", 1)[1].split("```", 1)[0]
            elif "```" in response:
                json_text = response.split("```", 1)[1].split("```", 1)[0]

            judgment = json.loads(json_text.strip())

            assert "relevant" in judgment
            assert "relevance_score" in judgment
            assert "reasoning" in judgment

            return judgment

        except Exception as e:
            print(f"      ⚠️  Failed to parse LLM response: {e}")
            return {
                "relevant": False,
                "relevance_score": 0,
                "reasoning": f"Failed to judge: {e}",
                "key_topics": [],
            }

    async def _save_result(self, result: Dict[str, Any], output_path: str):
        """
        Save filtered articles to markdown.

        Args:
            result: Dict with filtered_articles
            output_path: Path to save markdown
        """
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        articles = result["filtered_articles"]
        total_input = result["total_input"]
        total_output = result["total_output"]
        filter_rate = (total_output / total_input * 100) if total_input else 0.0

        with output.open("w", encoding="utf-8") as f:
            f.write("# Filtered AI/ML Articles\n\n")
            f.write(f"**Total Input:** {total_input}\n")
            f.write(f"**Total Output:** {total_output}\n")
            f.write(f"**Filter Rate:** {filter_rate:.1f}%\n\n")
            f.write("---\n\n")

            for article in articles:
                f.write(f"## {article['title']}\n\n")
                f.write(f"**URL:** {article['url']}\n")
                f.write(f"**Relevance Score:** {article['relevance_score']}/10\n")
                f.write(f"**Reasoning:** {article['reasoning']}\n")
                f.write(f"**Key Topics:** {', '.join(article['key_topics'])}\n\n")
                f.write(f"{article['summary']}\n\n")
                f.write("---\n\n")

        print(f"💾 Saved {len(articles)} filtered articles to {output}")
