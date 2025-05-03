# Achilles Optimizer Examples

This directory contains examples of using the Achilles optimizer in different scenarios.

## Setup

The examples have their own isolated environment managed by `uv`. To set up:

```bash
cd examples
uv venv
uv pip install -e ..
uv pip install -r requirements.txt  # If you have one, or use dependencies in pyproject.toml
```

## Running Examples

Examples can be run directly from this directory:

```bash
python testing.py
```

The `astronomy` directory contains domain-specific examples.
