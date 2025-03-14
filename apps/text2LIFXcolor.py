"""
Text to LIFX Image - Application for controlling LIFX lights with text prompts.

This application allows controlling LIFX lights through natural language text prompts.
It uses Claude to interpret text descriptions and convert them to light control commands.
"""

import random

from okabe import Nucleus
from okabe.nucleus import ToolSignature
from okabe.tools.lifx import Lifx, Light


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

    def set_light_color(self, light_id: str, hue: int) -> int:
        """
        Set the color of a specific light.

        Args:
            light_id: The ID of the light to control
            hue: The hue value to set (0-360)

        Returns:
            0 on success, 1 on failure
        """
        try:
            self.light_map[light_id].set_color(hue, 1.0, 1.0, 3500)
            return 0
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
    nucleus = Nucleus("Set a random LIFX bulb in my apartment to a random color 5 times")
    nucleus.add_tool_option(
        name="get_lights",
        description="Returns a list of LIFX light ids",
        callable=lm.get_lights,
        sig=[],
    )
    nucleus.add_tool_option(
        name="set_light_color",
        description="Set the color of a LIFX bulb, returns 0 on success and 1 other wise",
        callable=lm.set_light_color,
        sig=[
            ToolSignature(name="light_id", dtype="string", description="The id of the LIFX buld"),
            ToolSignature(
                name="hue",
                dtype="integer",
                description="The hue to change the light bulb to, value between 0-360",
            ),
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
