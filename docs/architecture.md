# Architecture Documentation

## System Overview

Multi-agent AI system for news aggregation and newsletter generation.

## Design Principles

1. **SOLID Principles**
   - Single Responsibility: Each agent has one job
   - Open/Closed: Easy to add new sources/agents
   - Dependency Inversion: Agents depend on abstractions

2. **Design Patterns**
   - Template Method: BaseAgent
   - Factory: FetcherFactory
   - Strategy: Rate limiting
   - Observer: Pipeline coordination

3. **Async-First**
   - All I/O is async
   - Concurrent fetching
   - Non-blocking operations

## Component Details

### 1. Fetchers (Milestone 1)

**Purpose:** Fetch articles from external sources

**Sources:**
- HackerNews API
- RSS feeds

**Key Features:**
- Async concurrent fetching
- Rate limiting (10 concurrent max)
- Error handling
- Markdown output

### 2. Agents (Milestones 3-4)

**BaseAgent:**
- Template Method pattern
- Consistent lifecycle: load → process → save
- LLM integration
- Tool support

**NewsFilterAgent:**
- Filters AI/ML relevant articles
- Uses Gemini for classification
- Returns relevance scores
- JSON output parsing

**SummarizerAgent:**
- Groups articles by topic
- Generates topic summaries
- Can use SearchSkill for context

**WriterAgent:**
- Writes engaging newsletter
- Professional tone
- Structured format

### 3. MCP Integration (Milestone 4)

**Database MCP Server:**
- Provides 3 tools: query, search, get_sources
- SQLite backend
- Stdio transport

**SearchSkill:**
- High-level abstraction over MCP
- Combines database search
- Reusable across agents

### 4. Pipeline Orchestration

**Flow:**
Fetch → Database → Filter → Summarize → Write


**Error Handling:**
- Each stage independent
- Graceful degradation
- Continue on errors

### 5. Evaluation (Milestone 5)

**Golden Dataset:**
- 10 hand-labeled examples
- Covers edge cases
- Balanced (5 relevant, 5 not)

**Metrics:**
- Accuracy: Overall correctness
- Precision: Relevant accuracy
- Recall: Find all relevant
- F1: Harmonic mean

## Data Flow

External APIs ↓
Fetchers (async) ↓
Markdown Files + Database ↓
FilterAgent (Gemini) ↓
Filtered Markdown ↓
SummarizerAgent (Gemini + SearchSkill) ↓
Summary Markdown ↓
WriterAgent (Gemini) ↓
Newsletter Markdown

## Technology Choices

**Why Python?**
- Excellent async support
- Rich AI/ML ecosystem
- Easy to learn and maintain

**Why Gemini?**
- Free tier generous
- Good function calling support
- Fast inference

**Why SQLite?**
- No server required
- Perfect for local development
- Easy to deploy

**Why MCP?**
- Industry standard emerging
- Tool reusability
- LLM-agnostic

**Why Markdown?**
- Human-readable
- Git-friendly
- Easy to debug
- Flexible format

## Performance

**Metrics:**
- Fetch 30 articles: ~2-3 seconds
- Filter 30 articles: ~30-45 seconds
- Complete pipeline: ~2-3 minutes

**Bottlenecks:**
- LLM API calls (rate limited)
- Network I/O

**Optimizations:**
- Concurrent fetching
- Rate limiting
- Caching (future)

## Security

**API Keys:**
- Stored in .env (not committed)
- Loaded at runtime
- Never logged

**Input Validation:**
- URL validation
- SQL injection prevention (parameterized queries)
- LLM output parsing (safe JSON)

**Rate Limiting:**
- Prevents API abuse
- Semaphore-based
- Configurable

## Future Enhancements

1. **More Sources**
   - Twitter API
   - Reddit
   - Research papers (arXiv)

2. **Better Evaluation**
   - Larger golden dataset
   - A/B testing framework
   - Human feedback loop

3. **Deployment**
   - Docker container
   - Scheduled runs (cron)
   - Web interface

4. **Advanced Features**
   - Semantic search
   - Personalization
   - Multi-language support