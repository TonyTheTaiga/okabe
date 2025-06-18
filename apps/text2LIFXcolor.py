"""
Text to LIFX Image - Application for controlling LIFX lights with text prompts.

This application allows controlling LIFX lights through natural language text prompts.
It uses Claude to interpret text descriptions and convert them to light control commands.
"""

import random
import json

from okabe import Nucleus
from okabe.nucleus import ToolSignature
from okabe.tools.lifx import Lifx, Light, decode_color_state


class LightManager:
    """
    Manages a collection of LIFX lights.

    This class provides methods for interacting with multiple LIFX lights,
    making it easier to control them as a group or individually.

    Attributes:
        lights: List of LIFX Light objects
        light_map: Dictionary mapping light IDs to Light objects
    """

    def __init__(self, lights: list[Light]):
        """
        Initialize a LightManager with a list of lights.

        Args:
            lights: List of LIFX Light objects to manage
        """
        self.lights = lights
        self.light_map = {light.target: light for light in self.lights}

    def get_lights(self) -> list[str]:
        """
        Get the IDs of all managed lights.

        Returns:
            List of light IDs as strings
        """
        return [light.target for light in self.lights]

    def update_light(
        self,
        light_id: str,
        hue: int,
        saturation: int,
        brightness: int,
        kelvin: int = 3500,
        duration: int = 0,
    ) -> int:
        """
        Set the color of a specific light.

        Args:
            light_id: The ID of the light to control
            hue: Hue value in degrees (0-360)
            saturation: Saturation value (0-100)
            brightness: Brightness value (0-100)
            kelvin: Color temperature in Kelvin (2500-9000)
            duration: Transition time in milliseconds (default: 0)

        Returns:
            0 on success, 1 on failure
        """
        try:
            self.light_map[light_id].set_color(
                hue, saturation / 100, brightness / 100, kelvin, duration
            )
            return 0
        except Exception as e:
            print(e)
            return 1

    def get_light(self, light_id: str) -> str:
        """
        Get the current state of a light.

        Args:
            light_id: The ID of the target light

        Returns:
            ON SUCCESS:
                str: A json str containing hue, saturation, brigthness, kelvin.

            ON FAILURE:
                int: 1
        """
        try:
            status = self.light_map[light_id].get_color()
            decoded = decode_color_state(status)
            decoded.pop("label")
            decoded.pop("power")
            return json.dumps(decoded)
        except Exception as e:
            print(e)
            return 1


def main():
    """
    Main entry point for the application.

    Discovers LIFX lights on the network, initializes the LightManager,
    and sets up a Nucleus agent to control lights with natural language.
    """
    lm = LightManager(lights=Lifx.discover())
    nucleus = Nucleus("Update my lights to be at 30% and blue")
    nucleus.add_tool_option(
        name="get_lights",
        description="Returns a list of LIFX light ids",
        callable=lm.get_lights,
        sig=[],
    )
    nucleus.add_tool_option(
        name="update_light",
        description="Set the color of a LIFX bulb, returns 0 on success and 1 other wise",
        callable=lm.update_light,
        sig=[
            ToolSignature(name="light_id", dtype="string", description="The id of the light bulb"),
            ToolSignature(
                name="hue",
                dtype="integer",
                description="The hue to change the light bulb to, value between 0-360",
            ),
            ToolSignature(
                name="saturation",
                dtype="integer",
                description="The saturation to change the light bulb to, value between 0-100",
            ),
            ToolSignature(
                name="brightness",
                dtype="integer",
                description="The brightness to change the light bulb to, value between 0-100",
            ),
            ToolSignature(
                name="kelvin",
                dtype="integer",
                description="The kelvin to change the light bulb to, value between 2500-9000",
            ),
            ToolSignature(
                name="duration",
                dtype="integer",
                description="The duration in milliseoncds that it will take for the light to transition to the new color",
            ),
        ],
    )
    nucleus.add_tool_option(
        name="get_light",
        description="get the current state of a light",
        callable=lm.get_light,
        sig=[
            ToolSignature(name="light_id", dtype="string", description="The id of the light bulb")
        ],
    )
    nucleus.add_tool_option(
        name="generate_random_int",
        description="Generate a random integer between specified bounds (inclusive)",
        callable=random.randint,
        sig=[
            ToolSignature(name="a", dtype="integer", description="lower bound for random integer"),
            ToolSignature(name="b", dtype="integer", description="upper bound for random integer"),
        ],
    )

    final = nucleus.run()
    print(final)


if __name__ == "__main__":
    main()
