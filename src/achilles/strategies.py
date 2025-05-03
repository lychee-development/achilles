from dataclasses import dataclass
from typing import List, Dict, Optional
import os
import json
import time

from achilles.prompts import (
    STANDARD_PROMPT,
    VECTORIZE_PROMPT,
    PARALLEL_PROMPT,
    MEMORY_PROMPT,
    ALGORITHMIC_PROMPT,
    METAL_GPU_PROMPT,
    NEON_PROMPT,
    CACHE_BLOCKING_PROMPT
)

@dataclass
class OptimizationStrategy:
    name: str
    description: str
    model: str  # LLM model to use
    prompt_template: str  # Specialized system prompt
    parameters: Dict  # Strategy-specific parameters
    
    def get_build_dir(self, base_dir: str) -> str:
        """Returns the directory for this strategy's build"""
        return os.path.join(base_dir, ".achilles", "strategies", self.name)

# Define built-in strategies
DEFAULT_STRATEGIES = {
    "standard-3-7": OptimizationStrategy(
        name="standard",
        description="Standard C++ optimization with Claude",
        model="claude-3-7-sonnet-20250219",
        prompt_template=STANDARD_PROMPT,
        parameters={"temperature": 0.2},
    ),
    "vectorize": OptimizationStrategy(
        name="vectorize",
        description="SIMD vectorization focused optimization",
        model="claude-3-7-sonnet-20250219",
        prompt_template=VECTORIZE_PROMPT,
        parameters={"temperature": 0.1},
    ),
    "algorithmic": OptimizationStrategy(
        name="algorithmic",
        description="Algorithmic optimization with Claude",
        model="claude-3-7-sonnet-20250219",
        prompt_template=ALGORITHMIC_PROMPT,
        parameters={"temperature": 0.2},
    ),
    "standard-3-5": OptimizationStrategy(
        name="standard",
        description="Standard C++ optimization with Claude",
        model="claude-3-5-sonnet-20241022",
        prompt_template=STANDARD_PROMPT,
        parameters={"temperature": 0.2},
    ),
    "memory": OptimizationStrategy(
        name="memory",
        description="Memory allocation optimization",
        model="claude-3-7-sonnet-20250219",
        prompt_template=MEMORY_PROMPT,
        parameters={"temperature": 0.2},
    ),
    "metal-gpu": OptimizationStrategy(
        name="metal_gpu",
        description="GPU optimisation via Metal on macOS (Clang)",
        model="claude-3-7-sonnet-20250219",
        prompt_template=METAL_GPU_PROMPT,
        parameters={"temperature": 0.15},
),
    "neon-simd": OptimizationStrategy(
        name="neon_simd",
        description="NEON SIMD optimisation for Apple Silicon",
        model="claude-3-7-sonnet-20250219",
        prompt_template=NEON_PROMPT,
        parameters={"temperature": 0.2},
    ),
    "cache-blocking": OptimizationStrategy(
        name="cache-blocking",
        description="Cache blocking and tiling for better memory locality",
        model="claude-3-7-sonnet-20250219",
        prompt_template=CACHE_BLOCKING_PROMPT,
        parameters={"temperature": 0.1},
    ),
}

def get_strategy(name: str) -> OptimizationStrategy:
    """Get a strategy by name"""
    if name in DEFAULT_STRATEGIES:
        return DEFAULT_STRATEGIES[name]
    raise ValueError(f"Unknown strategy: {name}")

def get_available_strategies() -> List[str]:
    """Get names of all available strategies"""
    return list(DEFAULT_STRATEGIES.keys())

class BenchmarkResult:
    def __init__(self, strategy_name: str, original_time: float, optimized_time: float):
        self.strategy_name = strategy_name
        self.original_time = original_time
        self.optimized_time = optimized_time
        self.speedup = original_time / optimized_time if optimized_time > 0 else 1.0
        self.improvement = (original_time - optimized_time) / original_time * 100

    def to_dict(self) -> Dict:
        return {
            "strategy": self.strategy_name,
            "original_time": self.original_time,
            "optimized_time": self.optimized_time,
            "speedup": self.speedup,
            "improvement": self.improvement
        }

def save_benchmark_results(results: List[BenchmarkResult], base_dir: str):
    """Save benchmark results to a JSON file"""
    results_dir = os.path.join(base_dir, ".achilles", "benchmarks")
    os.makedirs(results_dir, exist_ok=True)
    
    data = {
        "timestamp": time.time(),
        "results": [result.to_dict() for result in results]
    }
    
    with open(os.path.join(results_dir, "benchmark_results.json"), "w") as f:
        json.dump(data, f, indent=2)

def get_fastest_strategy(base_dir: str) -> Optional[str]:
    """Get the name of the fastest strategy based on benchmarks"""
    results_path = os.path.join(base_dir, ".achilles", "benchmarks", "benchmark_results.json")
    if not os.path.exists(results_path):
        return None
        
    with open(results_path, "r") as f:
        data = json.load(f)
    
    if not data.get("results"):
        return None
        
    fastest = min(data["results"], key=lambda x: x["optimized_time"])
    return fastest["strategy"]