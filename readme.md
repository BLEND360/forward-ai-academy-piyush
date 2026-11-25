# AI Agent Onboarding Project

Multi-agent news aggregation system with MCP integration

A production-ready AI agent pipeline that fetches, filters, summarizes, and writes AI/ML news newsletters.

## Features
🚀 Async News Fetching from multiple sources (HackerNews, RSS)
🤖 AI-Powered Filtering using LiteLLM with Qwen 3.5  
🤖 AI-Powered Filtering using LiteLLM with Qwen 3.5  
🔧 MCP Integration with reusable tools  
📝 Multi-Agent Pipeline (Filter → Summarize → Write)  
💾 SQLite Database for article storage  
📊 Evaluation Framework for quality measurement  
✅ 60%+ Test Coverage  

## Quick Start

### Prerequisites

- Python 3.11+
- OpenAI-compatible API endpoint (Qwen 3.5 or other)
- API key for the custom endpoint
- NewsAPI key (free tier)

### Installation

```bash
# Clone repo
git clone https://github.com/your-org/ai-agent-onboarding.git
cd ai-agent-onboarding

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your API keys and LiteLLM settings

# Example .env configuration:
# OPENAI_API_KEY=your_api_key
# OPENAI_BASE_URL=https://your-custom-endpoint.com/v1
# LITELLM_MODEL=qwen-3.5
# NEWSAPI_KEY=your_newsapi_key
```

### Run Complete Pipeline

```bash
# Run the complete pipeline
python src/complete_pipeline.py

# Output will be in:
# - data/output/newsletter.md (final newsletter)
# - data/context/ (intermediate outputs)
# - data/news_agent.db (article database)
```

### Run Individual Components

```bash
# Fetch articles only
python -m src.main

# Filter articles with AI
python src/pipeline.py

# Evaluate filtering quality
python src/evaluation/evaluator.py
```
```
┌─────────────────────────────────────────────┐
│         News Sources                        │
│  HackerNews | RSS Feeds | GitHub Trending   │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
        ┌──────────────────┐
        │ Fetch Orchestrator│
        │   (Milestone 1)   │
        └──────────┬────────┘
                   │
                   ▼
            ┌──────────┐
            │ Database │ ← MCP Server
            │ (SQLite) │
            └──────────┘
                   │
                   ▼
        ┌───────────────────┐
        │  FilterAgent      │
        └──────────┬────────┘
                   │
                   ▼
        ┌───────────────────┐
        │ SummarizerAgent   │
        │  (+ SearchSkill)  │
        └──────────┬────────┘
                   │
                   ▼
        ┌───────────────────┐
        │   WriterAgent     │
        │   (Newsletter)    │
        └──────────┬────────┘
                   │
                   ▼
           📄 Newsletter.md
Project Structure
ai-agent-onboarding/
├── src/
│   ├── agents/          # AI agents
│   │   ├── base_agent.py
│   │   ├── news_filter_agent.py
│   │   ├── summarizer_agent.py
│   │   └── writer_agent.py
│   ├── fetchers/        # News fetchers
│   ├── mcp/             # MCP servers
│   │   ├── database_server.py
│   │   └── simple_client.py
│   ├── skills/          # Reusable skills
│   │   └── search_skill.py
│   ├── database/        # Database management
│   ├── evaluation/      # Evaluation framework
│   └── complete_pipeline.py
├── tests/               # Test suite
├── data/
│   ├── articles/        # Fetched articles
│   ├── context/         # Agent outputs
│   ├── output/          # Final newsletter

```
## Key Technologies

- **Python 3.11+** - Core language
- **aiohttp** - Async HTTP requests
- **LiteLLM** - OpenAI-compatible LLM abstraction
- **Qwen 3.5** - Language model (via custom endpoint)
- **MCP** - Model Context Protocol
- **SQLite** - Local database
- **pytest** - Testing framework

## LiteLLM Configuration

This project uses LiteLLM to connect with OpenAI-compatible endpoints. The agent system is configured to work with any OpenAI-compatible API that supports Qwen 3.5 (or other models).

### Required Environment Variables

- `OPENAI_API_KEY` - API key for authentication
- `OPENAI_BASE_URL` - Base URL of your OpenAI-compatible endpoint (e.g., https://your-endpoint.com/v1)
- `LITELLM_MODEL` - Model name (e.g., qwen-3.5, qwen-7b, qwen-14b)

### Optional Environment Variables

- `OPENAI_API_BASE` - Alternative to OPENAI_BASE_URL
- `LITELLM_API_KEY` - Alternative to OPENAI_API_KEY
- `LITELLM_API_BASE` - Alternative to OPENAI_BASE_URL

### How It Works

All agents inherit from `BaseAgent` which automatically:

1. Reads model and endpoint configuration from environment variables
2. Normalizes model names for OpenAI-compatible endpoints
3. Uses `litellm.completion()` for synchronous calls
4. Uses `litellm.acompletion()` for asynchronous calls
5. Supports tool/function calling schema

### Example Setup

```bash
export OPENAI_API_KEY="your-api-key"
export OPENAI_BASE_URL="https://your-qwen-endpoint.com/v1"
export LITELLM_MODEL="qwen-3.5"
python src/complete_pipeline.py
```Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing

# Target: 60%+ coverage ✅
```

## Development

### Code Style

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint
pylint src/
```

### Adding New Sources

1. Create fetcher in `src/fetchers/`
2. Inherit from `BaseFetcher`
3. Implement `fetch_articles()` and `get_source_name()`
4. Register in `FetchOrchestrator`

### Adding New MCP Tools

1. Add tool schema to MCP server
2. Implement tool function
3. Register in `@server.call_tool()`
4. Test with MCP client

## License

MIT

## Acknowledgments

Built as part of AI Agent Onboarding curriculum (v3.3).
Acknowledgments
Built as part of AI Agent Onboarding curriculum (v3.3). ```
