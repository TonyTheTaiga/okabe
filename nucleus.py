import os
from typing import NamedTuple
import struct


from anthropic import Anthropic
from anthropic.types import ToolUseBlock, TextBlock
from dotenv import load_dotenv

from tools.lifx.lifx import Lifx

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


def get_weather(location: str):
    print(location)


def decode_color_state(data: bytes) -> dict:
    """
    Decode a LIFX light state packet.

    Args:
        data: Raw bytes data containing the light state

    Returns:
        Dictionary with decoded light state values

    Format:
        hue: Uint16
        saturation: Uint16
        brightness: Uint16
        kelvin: Uint16
        reserved6: 2 Reserved bytes
        power: Uint16
        label: 32 bytes String
        reserved7: 8 Reserved bytes
    """
    if len(data) < 52:
        raise ValueError(f"Not enough data to decode state: {len(data)} bytes, expected 52")

    hue, saturation, brightness, kelvin, power, label_bytes = struct.unpack("<HHHH2xH32s8x", data)
    label = label_bytes.split(b"\x00")[0].decode("utf-8")

    return {
        "hue": hue,
        "saturation": saturation,
        "brightness": brightness,
        "kelvin": kelvin,
        "power": power,
        "label": label,
    }


def encode_color_state(hue: int, saturation: int, brightness: int, kelvin: int, power: bool, label: str) -> bytes:
    """
    Encode light state values to binary data.

    Args:
        hue: Hue value (0-65535)
        saturation: Saturation value (0-65535)
        brightness: Brightness value (0-65535)
        kelvin: Color temperature (2500-9000)
        power: Power state (True/False)
        label: Light label (max 31 chars)

    Returns:
        Encoded bytes ready to be sent in a LIFX packet
    """
    encoded_label = label.encode("utf-8")
    if len(encoded_label) > 31:
        encoded_label = encoded_label[:31]

    encoded_label = encoded_label.ljust(32, b"\x00")
    power_value = 65535 if power else 0
    return struct.pack(
        "<HHHHH2xH32s8x",
        hue,
        saturation,
        brightness,
        kelvin,
        0,
        power_value,
        encoded_label,
    )


if __name__ == "__main__":
    # nucleus = Nucleus(task="What's the weather like in San Francisco?")
    # nucleus.add_tool_option(
    #     name="get_weather",
    #     description="Get the current weather in a given location",
    #     callable=get_weather,
    #     sig=[
    #         ToolSignature(
    #             name="location",
    #             dtype="string",
    #             description="The city and state, e.g. San Francisco, CA",
    #         ),
    #     ],
    # )

    # nucleus.run()

    lights = Lifx.discover()
    for light in lights:
        response = light.get_color()[0][2]
        print(response)
        print(response.packet_data)
        decoded = decode_color_state(response.packet_data)
        print(decoded)
