from __future__ import annotations
import binascii
import ipaddress
import socket
import struct
import logging
from typing import List, Tuple
import ifaddr
from .message import Message
from tools.lifx import message

DEVICE_PORT = 56700
SOCKET_TIMEOUT = 1


def get_broadcast_addresses() -> List[ipaddress.IPv4Address]:
    """
    Get all available broadcast addresses on the network interfaces.

    Discovers all network interfaces, filters out non-IPv4 and loopback addresses,
    and returns a list of broadcast addresses for each network.

    Returns:
        List of IPv4Address objects representing broadcast addresses
    """
    adapters = ifaddr.get_adapters()
    broadcast_addresses = []
    for adapter in adapters:
        for addr in adapter.ips:
            if not addr.is_IPv4:
                continue
            if addr.ip == "127.0.0.1":
                continue
            broadcast_addresses.append(
                ipaddress.IPv4Interface(f"{addr.ip}/{addr.network_prefix}").network.broadcast_address
            )
    return broadcast_addresses


class Lifx:
    """
    Main class for interacting with LIFX devices.

    Provides methods for discovering and communicating with LIFX devices on the network.
    """

    @staticmethod
    def discover() -> List[Light]:
        """
        Discover all LIFX devices on the local network.

        Sends a discovery message to all available broadcast addresses and creates
        Light objects for each device that responds.

        Returns:
            List of Light objects representing discovered LIFX devices
        """
        logging.info("discovering devices...")
        msg = Message.pack(pkt_type=2, source=2, tagged=1, res=1, ack=0, sequence=0)
        messages = Lifx.send(msg)
        lights = []
        for host, port, message in messages:
            lights.append(Light(message.target_hex, host, port))
        return lights

    @staticmethod
    def send(msg: Message) -> List[Message]:
        """
        Send a message to LIFX devices on the network.

        Creates a socket, sends the message to all broadcast addresses (filtering
        for "192.*" networks), and collects responses if required.

        Args:
            msg: The Message object to send

        Returns:
            List of Message objects representing responses from devices
        """
        sock = create_socket()
        messages = []
        broadcast_addresses = get_broadcast_addresses()
        for addr in broadcast_addresses:
            if not addr.exploded.startswith("192"):
                continue
            sock.sendto(msg.packed_msg, (addr.exploded, DEVICE_PORT))
            response = messages.extend(read(sock))
            if response:
                messages.extend(read(sock))

            sock.close()
        return messages


def read(sock: socket.socket) -> List[Tuple[str, int, Message]]:
    """
    Read responses from a socket.

    Waits for and unpacks messages received on the given socket.

    Args:
        sock: The socket to read from

    Returns:
        List of tuples containing (host, port, Message) for each response
    """
    responses = []
    data, (host, port) = sock.recvfrom(128)
    msg = Message.unpack(data)
    responses.append((host, port, msg))
    return responses


class Light:
    """
    Represents a LIFX light device.

    Provides methods for controlling and querying a specific LIFX light.

    Attributes:
        target_hex: The MAC address of the light as a byte string
        host: The IP address of the light
        port: The port to communicate with the light on
    """

    def __init__(self, target_hex: bytes, host: str, port: int) -> None:
        """
        Initialize a Light object.

        Args:
            target_hex: The MAC address of the light as a byte string
            host: The IP address of the light
            port: The port to communicate with the light on
        """
        self.target_hex = target_hex
        self.host = host
        self.port = port

    def get_power(self, res=0, ack=0) -> List[Message]:
        """
        Get the current power state of the light.

        Args:
            res: Flag indicating if response is required (default: 0)
            ack: Flag indicating if acknowledgment is required (default: 0)

        Returns:
            List of Message objects containing the power state
        """
        logging.info("getting power state...")
        msg = Message.pack(
            pkt_type=20,
            source=2,
            tagged=0,
            target=self.target_hex,
            sequence=0,
            res=res,
            ack=ack,
        )
        messages = Lifx.send(msg)
        return messages

    def set_power(self, on: bool) -> List[Message]:
        """
        Set the power state of the light.

        Args:
            on: True to turn the light on, False to turn it off
            res: Flag indicating if response is required (default: 0)
            ack: Flag indicating if acknowledgment is required (default: 0)

        Returns:
            List of Message objects containing responses (if any)
        """
        logging.info("setting power...")
        if on:
            level = 65535
        else:
            level = 0
        msg = Message.pack(
            pkt_type=21,
            source=2,
            tagged=0,
            target=self.target_hex,
            sequence=0,
            packet_data=struct.pack("<H", level),
            res=1,
            ack=0,
        )
        messages = Lifx.send(msg)
        return messages

    def get_color(self):
        msg = Message.pack(
            pkt_type=101,
            source=2,
            tagged=0,
            target=self.target_hex,  # pyright: ignore
            sequence=0,
            res=0,
            ack=0,
        )
        messages = Lifx.send(msg)
        return messages

    def set_color(self, hue, saturation, brightness, kelvin, duration=0) -> List[Message]:
        """
        Set the color of the light.

        Args:
            color: The color to set as a byte string

        Returns:
            List of Message objects containing responses (if any)

        Note:
            This method is not implemented yet.
        """

        packet_data = struct.pack(
            "<BHHHHI",
            0,
            int(round(0x10000 * hue) / 360) % 0x10000,
            int(round(0xFFFF * saturation)),
            int(round(0xFFFF * brightness)),
            kelvin,
            duration,
        )
        print(packet_data)
        msg = Message.pack(
            pkt_type=102,
            source=2,
            tagged=0,
            res=1,
            ack=0,
            sequence=0,
            target=self.target_hex,
            packet_data=packet_data,
        )
        res = Lifx.send(msg)
        return res

    @property
    def target(self) -> str:
        """
        Get the target MAC address as a hex string.

        Returns:
            The MAC address of the light as a hex string
        """
        return binascii.hexlify(self.target_hex).decode()


def create_socket() -> socket.socket:
    """
    Create a socket for communicating with LIFX devices.

    Creates a UDP socket, configures it for broadcast, sets a timeout,
    and binds it to a random port.

    Returns:
        A configured socket object ready for LIFX communication
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.settimeout(SOCKET_TIMEOUT)
    s.bind(("", 0))
    return s
