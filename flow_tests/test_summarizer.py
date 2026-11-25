import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from src.agents.summarizer_agent import SummarizerAgent


load_dotenv()


def _resolve_input_path() -> str:
    """Pick the first available filtered context file used in this project."""
    candidates = [
        Path("data/context/filtered_articles.md"),
        Path("data/context/enhanced_filtered.md"),
    ]
    for path in candidates:
        if path.exists():
            return str(path)
    raise FileNotFoundError("No filtered context file found in data/context")


def _configure_litellm_env() -> None:
    """Normalize environment variables so BaseAgent can configure LiteLLM."""
    model = os.getenv("LITELLM_MODEL") or os.getenv("OPENAI_MODEL")
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("LITELLM_API_KEY")
    api_base = (
        os.getenv("OPENAI_BASE_URL")
        or os.getenv("OPENAI_API_BASE")
        or os.getenv("LITELLM_API_BASE")
    )

    if model and not os.getenv("LITELLM_MODEL"):
        os.environ["LITELLM_MODEL"] = model

    if api_key and not os.getenv("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = api_key

    if api_base and not os.getenv("OPENAI_BASE_URL"):
        os.environ["OPENAI_BASE_URL"] = api_base

    if not api_key and not api_base:
        raise ValueError(
            "Set OPENAI_API_KEY (or LITELLM_API_KEY), or provide OPENAI_BASE_URL/OPENAI_API_BASE/LITELLM_API_BASE"
        )


async def test() -> None:
    _configure_litellm_env()

    agent = SummarizerAgent()
    await agent.execute(
        input_path=_resolve_input_path(),
        output_path="data/context/summary.md",
    )


if __name__ == "__main__":
    asyncio.run(test())
