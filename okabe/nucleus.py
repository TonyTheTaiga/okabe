"""
Nucleus module - Core framework for creating AI agents with tool-calling capabilities.

This module provides the infrastructure for creating AI assistants that can use
tools to control LIFX lights and potentially other devices.
"""

import json
import logging
import os
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Tuple

from anthropic import Anthropic
from anthropic.types import TextBlock, ToolUseBlock

logger = logging.getLogger(__name__)

try:
    from dotenv import load_dotenv

    load_dotenv()
except:
    logger.info("Make sure ANTHROPIC_API_KEY is set in your environment")

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY")


def chat(
    client: Anthropic,
    messages: List[Dict[str, Any]],
    tools: List[Dict[str, Any]],
    system: Optional[str] = None,
):
    """
    Send a message to the Claude API with tools.

    Args:
        client: Anthropic client instance
        messages: List of message objects with role and content
        tools: List of tool definitions
        system: Optional system prompt

    Returns:
        The response message from Claude
    """
    message = client.messages.create(
        messages=messages,
        tools=tools,
        max_tokens=1024,
        model="claude-3-5-sonnet-latest",
        system=system,
    )
    return message


class ToolSignature(NamedTuple):
    """
    Definition of a tool parameter.

    Attributes:
        name: Parameter name
        dtype: Parameter data type
        description: Human-readable description of the parameter
    """

    name: str
    dtype: str
    description: str


class Nucleus:
    """
    Core agent class that manages tools and communication with the LLM.

    The Nucleus class provides a framework for registering tools that Claude can use,
    and handles the conversation flow between the user, Claude, and the tool executions.
    """

    def __init__(self, task: str) -> None:
        """
        Initialize a new Nucleus agent.

        Args:
            task: The initial task for the agent to perform
        """
        self.task = task
        self._tools = []
        self._tool_map = {}
        self.client = Anthropic(api_key=ANTHROPIC_KEY)

    def add_tool_option(
        self, name: str, description: str, callable: Callable, sig: List[ToolSignature]
    ) -> None:
        """
        Register a new tool that the agent can use.

        Args:
            name: Name of the tool
            description: Human-readable description of what the tool does
            callable: Function to call when the tool is invoked
            sig: List of parameter definitions for the tool
        """
        self._tool_map[name] = callable
        self._tools.append((name, description, sig))

    def get_seed_prompt(self) -> List[Dict[str, Any]]:
        """
        Create the initial user message to start the conversation.

        Returns:
            A list containing the initial message object
        """
        return [
            {
                "role": "user",
                "content": f"Help me execute the follow task: {self.task}",
            },
        ]

    def run(self) -> str:
        """
        Run the agent conversation loop.

        This method starts the conversation with Claude, processes tool calls,
        and continues the conversation until completion.

        Returns:
            The final text response from Claude
        """
        run = True
        tools = self.compile_tools()
        messages = self.get_seed_prompt()
        system = "You are a helpful ai assistant with the ability to execute actions that require multiple turns as well as the ability to call tools"
        while run:
            completion = chat(client=self.client, messages=messages, tools=tools, system=system)
            messages.append({"role": "assistant", "content": completion.model_dump()["content"]})
            match completion.content:
                case [
                    TextBlock(
                        citations=text_block_citations, text=text_block_text, type=text_block_type
                    ),
                    ToolUseBlock(
                        id=tool_block_id,
                        name=tool_block_name,
                        input=tool_block_input,
                        type=tool_block_type,
                    ),
                ]:
                    tool_result = self._tool_map[tool_block_name](**tool_block_input)
                    logger.info("%s %s", text_block_text, tool_result)
                    messages.append(
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": tool_block_id,
                                    "content": json.dumps(tool_result),
                                },
                            ],
                        }
                    )
                case [
                    TextBlock(
                        citations=text_block_citations, text=text_block_text, type=text_block_type
                    ),
                ]:
                    return text_block_text
                case [
                    ToolUseBlock(
                        id=tool_block_id,
                        name=tool_block_name,
                        input=tool_block_input,
                        type=tool_block_type,
                    ),
                ]:
                    tool_result = self._tool_map[tool_block_name](**tool_block_input)
                    messages.append(
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": tool_block_id,
                                    "content": json.dumps(tool_result),
                                },
                            ],
                        }
                    )
                case _:
                    logger.info(completion.content)
                    logger.info("breaking...")
                    run = False

    def compile_tools(self) -> List[Dict[str, Any]]:
        """
        Convert the registered tools to the format expected by Claude's API.

        Returns:
            List of tool definitions ready to be passed to Claude
        """
        ret = []
        for name, description, sig in self._tools:
            ret.append(
                {
                    "name": name,
                    "description": description,
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            _sig.name: {"type": _sig.dtype, "description": _sig.description}
                            for _sig in sig
                        },
                    },
                }
            )

        return ret
