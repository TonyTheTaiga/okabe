"""
LIFX packet definitions module.

This module defines the different packet types used in the LIFX protocol,
along with their properties and methods for processing packet data.
"""

import struct
from typing import Dict, Type


class UnsupportedPacketType(Exception):
    """
    Exception raised when trying to use a packet type that is not supported.
    """

    pass


class Packet:
    """
    Base class for all LIFX packet types.

    This class provides a common interface for all packet types used in the LIFX protocol.
    Specific packet implementations should inherit from this class and define their
    own properties and methods for handling packet data.
    """

    use: str = ""
    pkt_type: int = 0


class SetPower(Packet):
    """
    Packet for setting the power state of a LIFX device.

    This packet is used to turn a light on or off. The level parameter determines
    the state (0 for off, 65535 for on).

    Attributes:
        use: The packet usage type ("SET")
        pkt_type: The packet type identifier (21)
        level: The power level data
    """

    use = "SET"
    pkt_type = 21

    def __init__(self, data: bytes):
        """
        Initialize a SetPower packet with the provided data.

        Args:
            data: The packet payload containing the power level
        """
        self.level = data[0:2]

    @property
    def payload(self) -> bytes:
        """
        Get the packet payload data.

        Returns:
            The power level as bytes
        """
        return self.level


class SetColor(Packet):
    """
    Packet for setting the color of a LIFX device.

    This packet is used to change the color, saturation, brightness, and temperature
    of a light.

    Attributes:
        use: The packet usage type ("SET")
        pkt_type: The packet type identifier (102)
    """

    use = "SET"
    pkt_type = 102


class StateService(Packet):
    """
    Packet containing service state information for a LIFX device.

    This packet is received in response to a GetService request and contains
    information about the service type and port.

    Attributes:
        use: The packet usage type ("STATE")
        pkt_type: The packet type identifier (3)
        bytes: The raw packet data
    """

    use = "STATE"
    pkt_type = 3

    def __init__(self, data: bytes):
        """
        Initialize a StateService packet with the provided data.

        Args:
            data: The packet payload containing service information
        """
        self.bytes = data

    @property
    def service(self) -> int:
        """
        Get the service type.

        Returns:
            The service type as an integer
        """
        return struct.unpack("<B", self.bytes[0:1])[0]

    @property
    def port(self) -> int:
        """
        Get the service port.

        Returns:
            The service port number
        """
        return struct.unpack("<I", self.bytes[1:])[0]


# Dictionary mapping packet type IDs to their corresponding packet classes
PACKETS: Dict[int, Type[Packet]] = {21: SetPower, 3: StateService}
