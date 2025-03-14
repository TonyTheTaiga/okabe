"""
Okabe - The World's Dumbest AI Agent

A simple framework for creating AI agents that can control LIFX smart lights
and potentially other devices.

This package provides tools for discovering and controlling LIFX lights through 
their UDP protocol, and a framework for creating AI agents with Claude that can
use these tools based on natural language instructions.
"""

from .nucleus import Nucleus, ToolSignature
