import os
import json
from typing import NamedTuple


from anthropic import Anthropic
from anthropic.types import ToolUseBlock, TextBlock

try:
    from dotenv import load_dotenv

    load_dotenv()
except:
    print("Make sure ANTHROPIC_API_KEY is set in your environment")

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY")


def chat(client, messages, tools, system=None):
    message = client.messages.create(
        messages=messages,
        tools=tools,
        max_tokens=1024,
        model="claude-3-5-sonnet-latest",
        system=system,
        temperature=0.7,
    )
    return message


class ToolSignature(NamedTuple):
    name: str
    dtype: str
    description: str


class Nucleus:
    def __init__(self, task: str) -> None:
        self.task = task
        self._tools = []
        self._tool_map = {}
        self.client = Anthropic(api_key=ANTHROPIC_KEY)

    def add_tool_option(self, name, description, callable, sig):
        self._tool_map[name] = callable
        self._tools.append((name, description, sig))

    def get_seed_prompt(self):
        return [
            {
                "role": "user",
                "content": f"Help me execute the follow task: {self.task}",
            },
        ]

    def run(self):
        run = True
        tools = self.compile_tools()
        messages = self.get_seed_prompt()
        system = "You are a helpful ai assistant with the ability to execute actions that require multiple turns as well as the ability to call tools"
        while run:
            completion = chat(client=self.client, messages=messages, tools=tools, system=system)
            messages.append({"role": "assistant", "content": completion.model_dump()["content"]})
            match completion.content:
                case [
                    TextBlock(citations=text_block_citations, text=text_block_text, type=text_block_type),
                    ToolUseBlock(id=tool_block_id, name=tool_block_name, input=tool_block_input, type=tool_block_type),
                ]:
                    tool_result = self._tool_map[tool_block_name](**tool_block_input)
                    print(text_block_text, tool_result)
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
                    TextBlock(citations=text_block_citations, text=text_block_text, type=text_block_type),
                ]:
                    return text_block_text
                case _:
                    print("breaking...")
                    run = False

    def compile_tools(self):
        ret = []
        for name, description, sig in self._tools:
            ret.append(
                {
                    "name": name,
                    "description": description,
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            _sig.name: {"type": _sig.dtype, "description": _sig.description} for _sig in sig
                        },
                    },
                }
            )

        return ret
