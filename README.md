<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://github.com/lychee-development/achilles/blob/main/dark.png?raw=true">
    <source media="(prefers-color-scheme: light)" srcset="https://github.com/lychee-development/achilles/blob/main/light.png?raw=true">
    <img alt="Achilles Logo" src="https://github.com/lychee-development/achilles/blob/main/light.png?raw=true" width="300" style="display: block; margin: 0 auto;">
  </picture>
</p>

-------------------------------------

# Achilles: LLM-powered Python performance optimizer


## How to use Achilles

Install Achilles using the following command:

```
uv add achilles-optimizer
```

Once Achilles is installed, you can optimize a python executable using the following command:

```
uv run achilles optimize your_python_file.py --your_python_args
```

If you've already ran Achilles once, you can benchmark it against the non-optimized python code with the following command:

```
uv run achilles benchmark your_python_file.py --your_python_args
```

To run a python executable using achillles, just type the following command:

```
uv run achilles run your_python_file.py --your_python_args
```

## Additional Information

### Requirements

- Python 3.13 or later
- [uv](https://github.com/astral-sh/uv) package manager
- An Anthropic API key (Claude)

### Environment Setup

You can set up your Anthropic API key in one of two ways:
1. Set the `ANTHROPIC_API_KEY` environment variable
2. Create a `.env` file in your project directory with the following content:
   ```
   ANTHROPIC_API_KEY=your_api_key_here
   ```

### How It Works

Achilles uses Claude to analyze your Python code and optimize its performance by:
- Identifying bottlenecks through profiling
- Implementing optimizations automatically in C++
- Importing these optimizations at runtime

### Command Reference

| Command | Description |
|---------|-------------|
| `uv run achilles optimize <file.py>` | Analyzes and optimizes your Python file |
| `uv run achilles benchmark <file.py>` | Compares optimized vs. original performance |
| `uv run achilles run <file.py>` | Runs your Python file with Achilles |

### Contributing

Contributions are welcome! Feel free to submit issues or pull requests on GitHub.

### License

This project is open source. See the repository for license details.
