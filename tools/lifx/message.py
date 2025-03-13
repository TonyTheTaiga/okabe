from __future__ import annotations
from typing import Union
import struct
import binascii

from pydantic import BaseModel

from .packet import Packet, PACKETS, UnsupportedPacketType

HEADER_SIZE = 36


def int_to_bits(value, size) -> str:
    return format(value, f"0>{size}b")


class IncompleteHeader(Exception):
    def __init__(self):
        super().__init__("Insufficient data to unpack a Header")


class FrameHeader(BaseModel):
    payload_size: int
    source: int
    tagged: int

    protocol: int = 1024
    addressable: int = 1
    origin: int = 0

    def __bytes__(self) -> bytes:
        encoded_size = struct.pack("<H", HEADER_SIZE + self.payload_size)
        encoded_flags = struct.pack(
            "<H",
            int(
                int_to_bits(self.origin, 2)
                + int_to_bits(self.tagged, 1)
                + int_to_bits(self.addressable, 1)
                + int_to_bits(self.protocol, 12),
                2,
            ),
        )
        encoded_source = struct.pack("<I", self.source)
        return encoded_size + encoded_flags + encoded_source


class FrameAddress(BaseModel):
    target: Union[int, bytes]
    res: int
    ack: int
    sequence: int

    def __bytes__(self) -> bytes:
        reserved = 0
        encoded_mac = self.convert_mac_to_bytes(self.target) + struct.pack("<H", 0)
        res = struct.pack("<I", 0) + struct.pack("<H", 0)
        encoded_flags = struct.pack(
            "<B",
            int(
                int_to_bits(reserved, 6)
                + int_to_bits(self.ack, 1)
                + int_to_bits(self.res, 1),
                2,
            ),
        )
        encoded_sequence = struct.pack("<B", self.sequence)

        return encoded_mac + res + encoded_flags + encoded_sequence

    def convert_mac_to_bytes(self, mac: Union[int, bytes]) -> str:
        if mac == 0:
            return struct.pack("<B", mac) * 6
        else:
            return mac


class ProtocolHeader(BaseModel):
    pkt_type: int

    def __bytes__(self) -> bytes:
        reserved = 0
        res_1 = struct.pack("<Q", reserved)
        encoded_type = struct.pack("<H", self.pkt_type)
        res_2 = struct.pack("<H", reserved)

        return res_1 + encoded_type + res_2


class Message:
    @classmethod
    def pack(
        kls,
        pkt_type: int,
        source: int,
        tagged: int,
        res: int,
        ack: int,
        sequence: int,
        target: int = 0,
        packet_data: bytes = b"",
    ):
        frame_header = FrameHeader(
            payload_size=len(packet_data), source=source, tagged=tagged
        )
        frame_address = FrameAddress(target=target, res=res, ack=ack, sequence=sequence)
        protocol_header = ProtocolHeader(pkt_type=pkt_type)

        return kls(
            header=bytes(frame_header) + bytes(frame_address) + bytes(protocol_header),
            packet_data=packet_data,
        )

    @classmethod
    def unpack(kls, data):
        if len(data) < 36:
            raise IncompleteHeader()
        return kls(header=data[:36], packet_data=data[36:])

    def __init__(self, header: bytes, packet_data: bytes):
        self.header = header
        self.packet_data = packet_data

        self._packet = None

    def __getitem__(self, byte_position) -> bytes:
        return self.header[byte_position]

    @property
    def packet(self) -> Packet:
        if not self._packet:
            t = PACKETS.get(self.pkt_type, None)

            if not t:
                raise UnsupportedPacketType(f"{self.pkt_type}")

            self._packet = t(data=self.packet_data)

        return self._packet

    @property
    def packed_msg(self) -> bytes:
        return self.header + self.packet_data

    @property
    def size(self) -> int:
        """returns the size of the total message."""
        return struct.unpack("<H", self[0:2])[0]

    @property
    def protocol(self) -> int:
        """returns the protocol version of the header."""
        v = struct.unpack("<H", self[2:4])[0]
        return v & 0b111111111111

    @property
    def addressable(self) -> bool:
        """returns whether the addressable bit is set."""
        v = self[3]
        v = v >> 4
        return (v & 0b1) != 0

    @property
    def tagged(self) -> bool:
        """returns whether the tagged bit is set."""
        v = self[3]
        v = v >> 5
        return (v & 0b1) != 0

    @property
    def source(self) -> int:
        """returns then number used by clients to differentiate themselves from other clients"""
        return struct.unpack("<I", self[4:8])[0]

    @property
    def target(self) -> str:
        """returns the target Serial from the header."""
        return binascii.hexlify(self[8:16][:6]).decode()

    @property
    def target_hex(self) -> bytes:
        return self[8:16][:6]

    @property
    def response_required(self) -> bool:
        """returns whether the response required bit is set in the header."""
        v = self[22]
        return (v & 0b1) != 0

    @property
    def ack_required(self) -> bool:
        """returns whether the ack required bit is set in the header."""
        v = self[22]
        v = v >> 1
        return (v & 0b1) != 0

    @property
    def sequence(self) -> int:
        """returns the sequence ID from the header."""
        return self[23]

    @property
    def pkt_type(self) -> int:
        """returns the Payload ID for the accompanying packet_data in the message."""
        return struct.unpack("<H", self[32:34])[0]
