from __future__ import annotations

import binascii
import ipaddress
import socket
import struct
import logging
from typing import List, Tuple

import ifaddr

from .message import Message

DEVICE_PORT = 56700
SOCKET_TIMEOUT = 1


def get_broadcast_addresses() -> List[ipaddress.IPv4Address]:
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
    @staticmethod
    def discover() -> List[Light]:
        logging.info("discovering devices...")
        msg = Message.pack(pkt_type=2, source=2, tagged=1, res=1, ack=0, sequence=0)
        messages = Lifx.send(msg)

        lights = []
        for host, port, message in messages:
            lights.append(Light(message.target_hex, host, port))

        return lights

    @staticmethod
    def send(msg: Message) -> List[Message]:
        sock = create_socket()

        messages = []
        broadcast_addresses = get_broadcast_addresses()
        print(broadcast_addresses)
        for addr in broadcast_addresses:
            if not addr.exploded.startswith("192"):
                continue

            sock.sendto(msg.packed_msg, (addr.exploded, DEVICE_PORT))

            if msg.response_required:
                messages.extend(read(sock))

            if msg.ack_required:
                messages.extend(read(sock))

            sock.close()

        return messages


def read(sock: socket.socket) -> Tuple[str, int, Message]:
    responses = []
    data, (host, port) = sock.recvfrom(128)
    msg = Message.unpack(data)
    responses.append((host, port, msg))

    return responses


class Light:
    def __init__(self, target_hex: bytes, host: str, port: int) -> None:
        self.target_hex = target_hex
        self.host = host
        self.port = port

    def set_power(self, on: bool, res=0, ack=0) -> List[Message]:
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
            res=res,
            ack=ack,
        )
        messages = Lifx.send(msg)
        return messages

    def set_color(self, color: bytes) -> List[Message]:
        pass

    @property
    def target(self) -> str:
        return binascii.hexlify(self.target_hex).decode()


def create_socket() -> socket.socket:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.settimeout(SOCKET_TIMEOUT)
    s.bind(("", 0))
    return s
