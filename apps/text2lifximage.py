from okabe import Nucleus
from okabe.nucleus import ToolSignature
from okabe.tools.lifx import Lifx, Light


class LightManager:
    def __init__(self, lights: list[Light]):
        self.lights = lights

    def get_lights(self) -> list[str]:
        return [light.target for light in self.lights]

    def set_light_color(self, light_id: str, color: str):
        print(light_id, color)


def main():
    lm = LightManager(lights=Lifx.discover())
    nucleus = Nucleus("Set a random LIFX bulb in my apartment to a random color")
    nucleus.add_tool_option(
        name="get_lights",
        description="Returns a list of LIFX light ids",
        callable=lm.get_lights,
        sig=[],
    )
    nucleus.add_tool_option(
        name="set_light_color",
        description="Set the color of a LIFX bulb",
        callable=lm.set_light_color,
        sig=[
            ToolSignature(name="light_id", dtype="string", description="The id of the LIFX buld"),
            ToolSignature(name="color", dtype="string", description="The color to change the light bulb to, in HEX"),
        ],
    )
    nucleus.run()


if __name__ == "__main__":
    main()
