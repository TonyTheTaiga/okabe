from okabe.nucleus import Nucleus
from okabe.tools.lifx import Lifx, Light


class LightManager:
    def __init__(self, lights: list[Light]):
        self.lights = lights

    def get_lights(self) -> list[str]:
        return [light.target for light in self.lights]


def main():
    lm = LightManager(lights=Lifx.discover())
    nucleus = Nucleus("Get all the lifx lights in my apartment")
    nucleus.add_tool_option(
        name="get_lights",
        description="Returns a list of LIFX light ids",
        callable=lm.get_lights,
        sig=[],
    )
    nucleus.run()


if __name__ == "__main__":
    main()
