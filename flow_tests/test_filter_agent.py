import asyncio
from dotenv import load_dotenv
from src.agents.news_filter_agent import NewsFilterAgent

load_dotenv()


async def test_filter():
    """Test filtering agent."""
    agent = NewsFilterAgent()
    
    # Use articles from Milestone 1
    result = await agent.execute(
        input_path="data/articles/all_articles.md",
        output_path="data/context/filtered_articles.md"
    )
    
    print(f"\n✅ Filtering complete!")
    print(f"   Input: {result['input_path']}")
    print(f"   Output: {result['output_path']}")


if __name__ == "__main__":
    asyncio.run(test_filter())