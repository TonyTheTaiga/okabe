# Okabe

## The World's Dumbest AI Agent

This is a WIP project to create the world's dumbest, least capable AI agent. While everyone else is trying to create super intelligent agents, I'm going in the opposite direction.

### What it does

Currently, Okabe can:
- Control LIFX smart lights through their UDP protocol
- Change colors, brightness, and power states
- Be controlled by Claude AI through a simple tool interface

### Why?

Because smart lights shouldn't need smart agents. The less intelligent the agent, the less it can do wrong.

### Current status

This is extremely early WIP. The LIFX protocol implementation works for basic light control, but the agent functionality is incomplete. The `Nucleus` class provides a framework for defining tools that Claude can use to control the lights.

### TODO

- Complete the agent implementation
- Add more device support
- Make it even dumber, somehow

### Requirements

- Python 3.9+
- A LIFX light on your local network
- An Anthropic API key for Claude integration

### Usage

Set your API key:
```bash
export ANTHROPIC_API_KEY=your_key_here
```

Then run:
```bash
python nucleus.py
```

Be amazed by how little it can accomplish!
