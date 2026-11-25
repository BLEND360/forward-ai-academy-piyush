# test_litellm.py
import os

import litellm
from dotenv import load_dotenv

load_dotenv()

model = os.getenv("LITELLM_MODEL") or os.getenv("OPENAI_MODEL")
api_key = os.getenv("OPENAI_API_KEY") or os.getenv("LITELLM_API_KEY")
api_base = (
	os.getenv("OPENAI_BASE_URL")
	or os.getenv("OPENAI_API_BASE")
	or os.getenv("LITELLM_API_BASE")
)

if not api_key and not api_base:
	raise ValueError("Set OPENAI_API_KEY (or LITELLM_API_KEY), or provide an OpenAI-compatible base URL")

if not api_key:
	api_key = "dummy-key"

if api_base and "/" not in model:
	model = f"openai/{model}"

response = litellm.completion(
	model=model,
	messages=[{"role": "user", "content": "Say hello!"}],
	api_key=api_key,
	api_base=api_base,
)

print(response.choices[0].message.content)
print("LiteLLM call working!")
