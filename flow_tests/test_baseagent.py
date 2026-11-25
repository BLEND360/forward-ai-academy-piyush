from src.agents.base_agent import BaseAgent
from dotenv import load_dotenv
import os

load_dotenv()

class TestAgent(BaseAgent):
    async def _load_context(self, input_path):
        return {"test": "data"}
    
    async def _process(self, context):
        response = await self._call_llm("Say hello")
        return {"response": response}
    
    async def _save_result(self, result, output_path):
        print(f"Would save: {result}")

# Test it
import asyncio
agent = TestAgent(model_name=os.getenv("LITELLM_MODEL") or os.getenv("OPENAI_MODEL") or "Qwen3.5-27B")
asyncio.run(agent.execute("input.md", "output.md"))