import os
from typing import NamedTuple


from anthropic import Anthropic
from anthropic.types import ToolUseBlock, TextBlock
from dotenv import load_dotenv


load_dotenv()


def chat(client, messages, tools):
    message = client.messages.create(
        messages=messages,
        tools=tools,
        max_tokens=1024,
        model="claude-3-5-sonnet-latest",
    )
    return message


class ToolSignature(NamedTuple):
    name: str
    dtype: str
    description: str


def compile_tools(tools: list):
    ret = []
    for name, description, sig in tools:
        ret.append(
            {
                "name": name,
                "description": description,
                "input_schema": {
                    "type": "object",
                    "properties": {_sig.name: {"type": _sig.dtype, "description": _sig.description} for _sig in sig},
                },
            }
        )

    return ret


class LLMCaller:
    def __init__(self): ...


class Nucleus:
    def __init__(self, task: str) -> None:
        self.task = task
        self._tools = []
        self._tool_map = {}

    def add_tool_option(self, name, description, callable, sig):
        self._tool_map[name] = callable
        self._tools.append((name, description, sig))

    def run(self):
        run = True
        client = Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY"),  # This is the default and can be omitted
        )
        messages = [
            {
                "role": "user",
                "content": self.task,
            },
        ]
        tools = compile_tools(self._tools)
        completion = chat(client, messages, tools)
        while run:
            for _content in completion.content:
                print(_content)
                fn_output = None
                text_output = None
                if isinstance(_content, ToolUseBlock):
                    fn = self._tool_map[_content.name]
                    fn_output = fn(**_content.input)  # pyright: ignore
                elif isinstance(_content, TextBlock):
                    text_output = _content.text

                print(fn_output, text_output)

            break
