"""
LIFX control module for the Okabe framework.

This module provides classes and utilities for discovering and controlling
LIFX smart lights through their UDP protocol.
"""

from .lifx import Lifx, Light, decode_color_state
from .message import Message
from .packet import PACKETS
