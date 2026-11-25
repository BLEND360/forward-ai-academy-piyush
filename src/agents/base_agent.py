"""Base class for AI agents."""

import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import litellm


class BaseAgent(ABC):
    """
    Base class for all AI agents.

    Implements Template Method pattern:
    - execute() orchestrates the workflow
    - Subclasses implement specific steps
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ):
        """
        Initialize agent.

        Args:
            model_name: LiteLLM model name, such as an OpenAI-compatible model.
            api_key: Optional API key override.
            api_base: Optional OpenAI-compatible base URL override.
        """
        self.model_name = (
            model_name
            or os.getenv("LITELLM_MODEL")
            or os.getenv("OPENAI_MODEL")
            or "gpt-4o-mini"
        )
        self.api_key = api_key
        self.api_base = api_base
        self.tools = tools or []
        self.model = None
        self.tool_functions = {}
        self.completion_kwargs: Dict[str, Any] = {}
        self._configure_model()

    def _configure_model(self):
        """Configure LiteLLM for an OpenAI-compatible endpoint."""
        api_key = (
            self.api_key or os.getenv("OPENAI_API_KEY") or os.getenv("LITELLM_API_KEY")
        )
        api_base = (
            self.api_base
            or os.getenv("OPENAI_BASE_URL")
            or os.getenv("OPENAI_API_BASE")
            or os.getenv("LITELLM_API_BASE")
        )

        if not api_key and not api_base:
            raise ValueError(
                "OPENAI_API_KEY (or LITELLM_API_KEY) not found in environment and no api_key override was provided"
            )

        if not api_key:
            api_key = "dummy-key"

        normalized_model = self.model_name
        if api_base and "/" not in normalized_model:
            normalized_model = f"openai/{normalized_model}"

        self.model = normalized_model
        self.completion_kwargs = {
            "model": normalized_model,
            "api_key": api_key,
        }

        if self.tools:
            self.completion_kwargs["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool_schema["name"],
                        "description": tool_schema.get("description", ""),
                        "parameters": tool_schema.get(
                            "parameters", {"type": "object", "properties": {}}
                        ),
                    },
                }
                for tool_schema in self.tools
            ]

        if api_base:
            self.completion_kwargs["api_base"] = api_base

    def register_tool_function(self, name: str, function):
        """Register actual function for a tool."""
        self.tool_functions[name] = function

    def _call_llm_with_tools(self, prompt: str) -> str:
        """
        Call LLM with tool metadata enabled.

        This lightweight helper keeps behavior synchronous for compatibility.
        """
        response = litellm.completion(
            messages=[{"role": "user", "content": prompt}],
            **self.completion_kwargs,
        )

        choice = response.choices[0]
        message = getattr(choice, "message", None)

        if message and getattr(message, "content", None):
            return message.content

        if getattr(choice, "text", None):
            return choice.text

        return ""

    async def execute(self, input_path: str, output_path: str) -> Dict[str, Any]:
        """
        Execute agent workflow (Template Method).

        Steps:
        1. Load input context
        2. Process with LLM
        3. Save results

        Args:
            input_path: Path to input markdown file
            output_path: Path to save output

        Returns:
            Result metadata
        """
        print(f"\n🤖 {self.__class__.__name__} starting...")

        # Step 1: Load
        context = await self._load_context(input_path)

        # Step 2: Process
        result = await self._process(context)

        # Step 3: Save
        await self._save_result(result, output_path)

        print(f"✅ {self.__class__.__name__} complete")

        return {"input_path": input_path, "output_path": output_path, "success": True}

    @abstractmethod
    async def _load_context(self, input_path: str) -> Dict[str, Any]:
        """
        Load input context.

        Subclasses implement how to read their input.
        """
        pass

    @abstractmethod
    async def _process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process context with LLM.

        Subclasses implement their specific logic.
        """
        pass

    @abstractmethod
    async def _save_result(self, result: Dict[str, Any], output_path: str):
        """
        Save processing result.

        Subclasses implement how to save their output.
        """
        pass

    async def _call_llm(self, prompt: str) -> str:
        """
        Call LiteLLM with prompt.

        Helper method for subclasses.

        Args:
            prompt: Prompt to send

        Returns:
            LLM response text
        """
        try:
            response = await litellm.acompletion(
                messages=[{"role": "user", "content": prompt}],
                **self.completion_kwargs,
            )

            choice = response.choices[0]
            message = getattr(choice, "message", None)

            if message and getattr(message, "content", None):
                return message.content

            if getattr(choice, "text", None):
                return choice.text

            return ""
        except Exception as e:
            print(f"❌ LLM call failed: {e}")
            raise
