# Okabe

The World's Greatest AI Agent Framework

![Mad Scientist](okabe.webp)

## What it does

Okabe is a lightweight framework for creating AI agents with simple tools.
The core concept is a minimal agent that:

- Makes it easy to define new tools and capabilities
- Connects LLMs to physical devices and services

Currently implemented tools:

- LIFX smart light control through UDP protocol (first tool implemented)
- More tools coming soon!

### Installation

1. Clone the repository
2. Install the package in development mode:

```bash
pip install -e .
```

### Usage

Set your API key:

```bash
export ANTHROPIC_API_KEY=your_key_here
```

### Applications

#### text2LIFXcolor

lets you control your lifx bulbs with natural language

```bash
python apps/text2LIFXcolor.py
```

### Building Agentic Applications with Nucleus

The `Nucleus` class provides a simple framework for building agentic applications. Here's how to use it:

```python
from okabe import Nucleus
from okabe.nucleus import ToolSignature

# 1. Initialize Nucleus with a task description
nucleus = Nucleus("Task description for the Agent to perform")

# 2. Register tools with their signatures
nucleus.add_tool_option(
    name="tool_name",
    description="Human-readable description of what the tool does",
    callable=your_function,  # Function to call when tool is invoked
    sig=[
        ToolSignature(name="param1", dtype="string", description="Parameter description"),
        ToolSignature(name="param2", dtype="integer", description="Parameter description"),
    ]
)

# 3. Run the agent and get the final response
result = nucleus.run()
```

### Adding New Tools

The framework is designed to make it easy to add new tools to do whatever you want

1. Create a new module in the `tools` directory
2. Implement the core functionality for your device/service
3. Use the `Nucleus.add_tool_option` to register your tools
