import struct


class UnsupportedPacketType(Exception):
    pass


class Packet:
    pass


class SetPower(Packet):
    use = "SET"
    pkt_type = 21

    def __init__(self, data: bytes):
        # Check for unsupported values
        self.level = data[0:2]

    @property
    def payload(self) -> bytes:
        return self.level


class SetColor(Packet):
    use = "SET"
    pkt_type = 102


class StateService(Packet):
    use = "STATE"
    pkt_type = 3

    def __init__(self, data: bytes):
        self.bytes = data

    @property
    def service(self) -> int:
        return struct.unpack("<B", self.bytes[0:1])[0]

    @property
    def port(self) -> int:
        return struct.unpack("<I", self.bytes[1:])[0]


PACKETS = {21: SetPower, 3: StateService}
