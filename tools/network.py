from typing import List
import ipaddress

import ifaddr


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
                ipaddress.IPv4Interface(
                    f"{addr.ip}/{addr.network_prefix}"
                ).network.broadcast_address
            )

    return broadcast_addresses


BROADCAST_ADDRS = get_broadcast_addresses()

print(BROADCAST_ADDRS)
