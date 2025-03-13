from __future__ import annotations
from typing import Union
import struct
import binascii

from pydantic import BaseModel

from .packet import Packet, PACKETS, UnsupportedPacketType

HEADER_SIZE = 36


def int_to_bits(value, size) -> str:
    """
    Convert an integer value to a binary string representation with leading zeros.

    Args:
        value: The integer value to convert
        size: The number of bits the binary string should have

    Returns:
        A string representation of the value in binary with specified bit length
    """
    return format(value, f"0>{size}b")


class IncompleteHeader(Exception):
    """
    Exception raised when there is insufficient data to unpack a message header.
    """

    def __init__(self):
        super().__init__("Insufficient data to unpack a Header")


class FrameHeader(BaseModel):
    """
    Represents the frame header portion of a LIFX protocol message.

    The frame header contains information about the message size, protocol version,
    source identifier, and addressing mode.

    Attributes:
        payload_size: Size of the message payload in bytes
        source: Source identifier used to differentiate clients
        tagged: Flag indicating if the message is tagged (1) or not (0)
        protocol: Protocol version (default: 1024)
        addressable: Flag indicating if the message is addressable (default: 1)
        origin: Origin of the message (default: 0)
    """

    payload_size: int
    source: int
    tagged: int

    protocol: int = 1024
    addressable: int = 1
    origin: int = 0

    def __bytes__(self) -> bytes:
        """
        Convert the frame header to its binary representation.

        Returns:
            Bytes representation of the frame header
        """
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
    """
    Represents the frame address portion of a LIFX protocol message.

    The frame address contains information about the target device, acknowledgment
    requirements, and sequence number for message ordering.

    Attributes:
        target: MAC address of the target device as bytes or an integer (0 for all devices)
        res: Flag indicating if a response is required
        ack: Flag indicating if acknowledgment is required
        sequence: Sequence number for message ordering
    """

    target: Union[int, bytes]
    res: int
    ack: int
    sequence: int

    def __bytes__(self) -> bytes:
        """
        Convert the frame address to its binary representation.

        Returns:
            Bytes representation of the frame address
        """
        reserved = 0
        encoded_mac = self.convert_mac_to_bytes(self.target) + struct.pack("<H", 0)
        res = struct.pack("<I", 0) + struct.pack("<H", 0)
        encoded_flags = struct.pack(
            "<B",
            int(
                int_to_bits(reserved, 6) + int_to_bits(self.ack, 1) + int_to_bits(self.res, 1),
                2,
            ),
        )
        encoded_sequence = struct.pack("<B", self.sequence)

        return encoded_mac + res + encoded_flags + encoded_sequence

    def convert_mac_to_bytes(self, mac: Union[int, bytes]) -> bytes:
        """
        Convert a MAC address to its byte representation.

        Args:
            mac: MAC address as an integer or bytes

        Returns:
            Byte representation of the MAC address
        """
        if mac == 0:
            return struct.pack("<B", mac) * 6
        else:
            return mac


class ProtocolHeader(BaseModel):
    """
    Represents the protocol header portion of a LIFX protocol message.

    The protocol header contains information about the packet type.

    Attributes:
        pkt_type: The packet type identifier
    """

    pkt_type: int

    def __bytes__(self) -> bytes:
        """
        Convert the protocol header to its binary representation.

        Returns:
            Bytes representation of the protocol header
        """
        reserved = 0
        res_1 = struct.pack("<Q", reserved)
        encoded_type = struct.pack("<H", self.pkt_type)
        res_2 = struct.pack("<H", reserved)

        return res_1 + encoded_type + res_2


class Message:
    """
    Represents a complete LIFX protocol message.

    A message consists of a header and payload data. The header is composed of
    a frame header, frame address, and protocol header. The payload contains the
    actual packet data being transmitted.

    This class provides methods for packing and unpacking LIFX protocol messages,
    as well as accessing various header fields.
    """

    def __init__(self, header: bytes, packet_data: bytes):
        """
        Initialize a Message with the provided header and packet data.

        Args:
            header: Binary header data
            packet_data: Binary payload data
        """
        self.header = header
        self.packet_data = packet_data

        self._packet = None

    @classmethod
    def pack(
        cls,
        pkt_type: int,
        source: int,
        tagged: int,
        res: int,
        ack: int,
        sequence: int,
        target: int = 0,
        packet_data: bytes = b"",
    ):
        """
        Create a new Message by packing the provided parameters.

        Args:
            pkt_type: Packet type identifier
            source: Source identifier
            tagged: Flag indicating if the message is tagged
            res: Flag indicating if a response is required
            ack: Flag indicating if acknowledgment is required
            sequence: Sequence number for message ordering
            target: Target device MAC address (default: 0 for all devices)
            packet_data: Payload data bytes (default: empty bytes)

        Returns:
            A new Message instance with the specified parameters
        """
        frame_header = FrameHeader(payload_size=len(packet_data), source=source, tagged=tagged)
        frame_address = FrameAddress(target=target, res=res, ack=ack, sequence=sequence)
        protocol_header = ProtocolHeader(pkt_type=pkt_type)

        return cls(
            header=bytes(frame_header) + bytes(frame_address) + bytes(protocol_header),
            packet_data=packet_data,
        )

    @classmethod
    def unpack(cls, data):
        """
        Create a new Message by unpacking the provided binary data.

        Args:
            data: Binary data to unpack

        Returns:
            A new Message instance unpacked from the data

        Raises:
            IncompleteHeader: If the data is too short to contain a complete header
        """
        if len(data) < 36:
            raise IncompleteHeader()

        return cls(header=data[:36], packet_data=data[36:])

    def __getitem__(self, byte_position) -> bytes:
        """
        Get a byte or slice of bytes from the header.

        Args:
            byte_position: Index or slice to retrieve

        Returns:
            Byte(s) at the specified position in the header
        """
        return self.header[byte_position]

    @property
    def packet(self) -> Packet:
        """
        Get the packet instance for this message.

        Returns:
            The packet instance for this message

        Raises:
            UnsupportedPacketType: If the packet type is not supported
        """
        if not self._packet:
            t = PACKETS.get(self.pkt_type, None)

            if not t:
                raise UnsupportedPacketType(f"{self.pkt_type}")

            self._packet = t(data=self.packet_data)

        return self._packet

    @property
    def packed_msg(self) -> bytes:
        """
        Get the complete packed message.

        Returns:
            The complete message as bytes (header + payload)
        """
        return self.header + self.packet_data

    @property
    def size(self) -> int:
        """
        Get the total size of the message.

        Returns:
            The total size of the message in bytes
        """
        return struct.unpack("<H", self[0:2])[0]

    @property
    def protocol(self) -> int:
        """
        Get the protocol version from the header.

        Returns:
            The protocol version
        """
        v = struct.unpack("<H", self[2:4])[0]
        return v & 0b111111111111

    @property
    def addressable(self) -> bool:
        """
        Check if the addressable bit is set in the header.

        Returns:
            True if the message is addressable, False otherwise
        """
        v = self[3]
        v = v >> 4
        return (v & 0b1) != 0

    @property
    def tagged(self) -> bool:
        """
        Check if the tagged bit is set in the header.

        Returns:
            True if the message is tagged, False otherwise
        """
        v = self[3]
        v = v >> 5
        return (v & 0b1) != 0

    @property
    def source(self) -> int:
        """
        Get the source identifier from the header.

        Returns:
            The source identifier
        """
        return struct.unpack("<I", self[4:8])[0]

    @property
    def target(self) -> str:
        """
        Get the target MAC address from the header as a hex string.

        Returns:
            The target MAC address as a hex string
        """
        return binascii.hexlify(self[8:16][:6]).decode()

    @property
    def target_hex(self) -> bytes:
        """
        Get the target MAC address from the header as raw bytes.

        Returns:
            The target MAC address as bytes
        """
        return self[8:16][:6]

    @property
    def response_required(self) -> bool:
        """
        Check if the response required bit is set in the header.

        Returns:
            True if a response is required, False otherwise
        """
        v = self[22]
        return (v & 0b1) != 0

    @property
    def ack_required(self) -> bool:
        """
        Check if the acknowledgment required bit is set in the header.

        Returns:
            True if acknowledgment is required, False otherwise
        """
        v = self[22]
        v = v >> 1
        return (v & 0b1) != 0

    @property
    def sequence(self) -> int:
        """
        Get the sequence number from the header.

        Returns:
            The sequence number
        """
        return self[23]

    @property
    def pkt_type(self) -> int:
        """
        Get the packet type from the header.

        Returns:
            The packet type identifier
        """
        return struct.unpack("<H", self[32:34])[0]
