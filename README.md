<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://github.com/lychee-development/achilles/blob/main/dark.png?raw=true">
    <source media="(prefers-color-scheme: light)" srcset="https://github.com/lychee-development/achilles/blob/main/light.png?raw=true">
    <img alt="Achilles Logo" src="https://github.com/lychee-development/achilles/blob/main/light.png?raw=true" width="300" style="display: block; margin: 0 auto;">
  </picture>
</p>

-------------------------------------

# Achilles: LLM-powered Python performance optimizer

Achilles is a tool that automatically speeds up your Python programs by rewriting the bottlenecks in C++ with the help of LLMs. 

### How It Works

Achilles uses Claude to analyze your Python code and optimize its performance by:
1. **Profiling** your Python code with cProfile to identify slow functions 🐢
2. Then it **generates multiple optimized C++ versions** of those functions using multiple different strategies 🚀
3. **Benchmarks** the different strategies against one another and **validates** the strategy output against the original code 🗒️
4. And finally **compiles and patches** them in at runtime 🧵


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

We have some example projects you can run in the repository, in the examples folder.

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

We have some agents which use different strategies for speeding up your code
| Strategy       | Description                                            | Use Case                                    |
| -------------- | ------------------------------------------------------ | ------------------------------------------- |
| **standard**       | Safe, general-purpose C++ translation                  | Generic code                                |
| **algorithmic**    | Attempts to rewrite with better algorithmic efficiency | More algorithmic tasks                      |
| **vectorize**      | SIMD vectorization                                     | Loops, machine learning, linear algebra     |
| **neon-simd**      | Uses NEON intrinsics for Apple Silicon devices         | Loops, machine learning, linear algebra     |
| **memory**         | Reduces allocations and copies                         | Memory-intensive workloads                  |
| **parallel**       | Adds multithreading                                    | Parallelizable code on the CPU              |
| **metal-gpu**      | Moves hot loops to Metal GPU on macOS                  | Parallelizable code on the GPU              |
| **cache-blocking** | Applies loop tiling for cache reuse                    | Image/matrix processing                     |

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
