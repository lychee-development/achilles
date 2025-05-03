import os
import subprocess
import sys
import time
import random
import concurrent.futures
from functools import partial
from achilles.profiling import get_code_benchmark, profile_via_subprocess
from achilles.agents.analysis_agent import select_functions
from achilles.agents.cpp_agent import optimize_functions
from achilles.data_models import build_cpp_modules, apply_optimizations
from achilles.printers import (
    print_header, print_check, print_warning, print_error,
    print_detail, SpinnerContext, print_optimization_complete,
    print_optimization_stats
)
from achilles.strategies import (BenchmarkResult, save_benchmark_results, get_available_strategies)
def achilles_build_exists() -> bool:
    """
    Check if a file named 'achilles_build' exists in the current working directory.
    """
    return os.path.isfile("achilles_build")

def run(args):
    """Run with the optimal strategy automatically"""
    if not achilles_build_exists():
        print_error("No Achilles Build Exists! Run 'achilles optimize' first.")
        return
    
    # Read the active/fastest strategy
    with open("achilles_build", "r") as f:
        strategy_name = f.read().strip()
    
    print_detail(f"Using optimization strategy: {strategy_name}")
    
    # Apply optimizations with the best strategy
    if apply_optimizations(strategy_name):
        subprocess.run([sys.executable] + args)

def optimize_with_strategy(strategy_name, selected_funcs, args, original_time, base_dir):
    """Worker function to optimize using a specific strategy"""
    try:
        print_header(f"OPTIMIZING WITH {strategy_name.upper()}", "🔄")
        
        # Optimization phase with this strategy
        optimized_funcs = []
        for i, func in enumerate(selected_funcs, 1):
            func_name = func.func
            print(f"Generating C++ code for {func_name} with {strategy_name}... ({i}/{len(selected_funcs)})")
            opt_func = optimize_functions([func], strategy_name)[0]
            optimized_funcs.append(opt_func)
            
            # Show some details about what's being optimized
            if "matrix" in func_name.lower() or "multiply" in func_name.lower():
                print_detail("Heavy numerical computation detected")
            elif "recursive" in func_name.lower() or "fibonacci" in func_name.lower():
                print_detail("Recursive function detected")
            
        # Building phase
        print_header(f"BUILDING {strategy_name.upper()}", "🔧")
        build_cpp_modules(optimized_funcs, strategy_name)
        
        # Benchmark this strategy
        print_header(f"BENCHMARKING {strategy_name.upper()}", "📊")
        start_time = time.time()
        if apply_optimizations(strategy_name):
            subprocess.run([sys.executable] + args, check=True, capture_output=True)
        optimized_time = time.time() - start_time
        
        # Calculate and return results
        if original_time > 0:
            speedup = original_time / optimized_time if optimized_time > 0 else 1.0
            improvement = (original_time - optimized_time) / original_time * 100
            
            result = BenchmarkResult(
                strategy_name=strategy_name,
                original_time=original_time,
                optimized_time=optimized_time
            )
            return result
        
    except Exception as e:
        print_error(f"Error with strategy {strategy_name}: {str(e)}")
        return None

def optimize(args, use_parallel=True):
    """Optimize and benchmark all strategies, optionally in parallel"""
    
    # Analysis phase (common to all strategies)
    print_header("ANALYZING CODE", "🔍")
    with SpinnerContext("Running profiler..."):
        unoptimized_funcs = get_code_benchmark(args)
    print_check("Running profiler...")
    with SpinnerContext("Identifying bottlenecks..."):
        selected_funcs = select_functions(unoptimized_funcs)
    print_check("Identifying bottlenecks...")
    
    if not selected_funcs:
        print_error("No suitable functions found for optimization.")
        return
    
    print_warning(f"Found {len(selected_funcs)} optimization candidates")
    
    # Track benchmark results for all strategies
    benchmark_results = []
    base_dir = os.path.abspath(os.getcwd())
    
    # Get baseline execution time once
    with SpinnerContext("Measuring baseline performance..."):
        start_time = time.time()
        original_stats = profile_via_subprocess(args)
        original_time = time.time() - start_time
    print_check("Baseline performance measured")
    
    # Get all strategies
    strategies = get_available_strategies()
    
    if use_parallel:
        print_header("PARALLEL OPTIMIZATION", "⚡")
        print(f"Running {len(strategies)} optimization strategies in parallel...")
        
        # Create a partial function with fixed arguments
        worker_func = partial(
            optimize_with_strategy, 
            selected_funcs=selected_funcs, 
            args=args, 
            original_time=original_time,
            base_dir=base_dir
        )
        
        # Use ProcessPoolExecutor to run strategies in parallel
        with concurrent.futures.ProcessPoolExecutor() as executor:
            # Submit all optimization tasks
            future_to_strategy = {
                executor.submit(worker_func, strategy_name): strategy_name 
                for strategy_name in strategies
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_strategy):
                strategy_name = future_to_strategy[future]
                try:
                    result = future.result()
                    if result is not None:
                        benchmark_results.append(result)
                        print_check(f"{strategy_name} optimization complete")
                        print_optimization_stats({
                            f"{strategy_name} execution time": f"{result.optimized_time:.4f}s",
                            "Original execution time": f"{original_time:.4f}s",
                            "Speedup": f"{result.speedup:.1f}×",
                            "Improvement": f"{result.improvement:.2f}%"
                        })

                except Exception as exc:
                    print_error(f"{strategy_name} generated an exception: {exc}")

    else:
        # Sequential processing
        print_header("SEQUENTIAL OPTIMIZATION", "🔄")
        print(f"Running {len(strategies)} optimization strategies sequentially...")
        
        for strategy_name in strategies:
            try:
                result = optimize_with_strategy(
                    strategy_name, 
                    selected_funcs, 
                    args, 
                    original_time, 
                    base_dir
                )
                if result is not None:
                    benchmark_results.append(result)
                    print_check(f"{strategy_name} optimization complete")
                    print_optimization_stats({
                        f"{strategy_name} execution time": f"{result.optimized_time:.4f}s",
                        "Original execution time": f"{original_time:.4f}s",
                        "Speedup": f"{result.speedup:.1f}×",
                        "Improvement": f"{result.improvement:.2f}%"
                    })
            except Exception as e:
                print_error(f"Error with strategy {strategy_name}: {str(e)}")
    
    if benchmark_results:
        # Save benchmark results
        save_benchmark_results(benchmark_results, base_dir)
        
        # Find the fastest strategy
        fastest = min(benchmark_results, key=lambda r: r.optimized_time)
        
        print_header("OPTIMIZATION SUMMARY", "🏆")
        print_optimization_complete(f"{fastest.speedup:.1f}")
        
        # Sort strategies by performance
        sorted_results = sorted(benchmark_results, key=lambda r: r.optimized_time)
        
        print("\nStrategy Performance Ranking:")
        for i, result in enumerate(sorted_results, 1):
            print(f"{i}. {result.strategy_name}: {result.speedup:.1f}× speedup ({result.improvement:.1f}% faster)")
        
        # Set the fastest strategy as active
        with open(os.path.join(base_dir, "achilles_build"), "w") as f:
            f.write(fastest.strategy_name)
        
        print(f"\nFastest strategy is {fastest.strategy_name} with {fastest.speedup:.1f}× speedup")
        print("Run your code with 'achilles run' to use the fastest strategy automatically.")

def benchmark(args, use_parallel=True):
    """Compare performance of all available strategies, optionally in parallel"""
    
    base_dir = os.path.abspath(os.getcwd())
    strategies_dir = os.path.join(base_dir, ".achilles", "strategies")
    
    if not os.path.exists(strategies_dir):
        print_error("No optimized builds found. Run 'achilles optimize' first.")
        return
    
    # Find all built strategies
    strategy_names = []
    for name in os.listdir(strategies_dir):
        strategy_path = os.path.join(strategies_dir, name)
        if os.path.isdir(strategy_path) and os.path.exists(os.path.join(strategy_path, "achilles_build")):
            strategy_names.append(name)
    
    if not strategy_names:
        print_error("No built strategies found. Run 'achilles optimize' first.")
        return
    
    print_header("BENCHMARKING", "📊")
    
    # First run the original code to get baseline
    with SpinnerContext("Running original code..."):
        start_time = time.time()
        original_stats = profile_via_subprocess(args)
        original_time = time.time() - start_time
    print_check("Original code execution complete")
    
    # Function to benchmark a single strategy
    def benchmark_strategy(strategy_name):
        try:
            print(f"Benchmarking {strategy_name}...")
            start_time = time.time()
            if apply_optimizations(strategy_name):
                subprocess.run([sys.executable] + args, check=True, capture_output=True)
            optimized_time = time.time() - start_time
            
            result = BenchmarkResult(
                strategy_name=strategy_name,
                original_time=original_time,
                optimized_time=optimized_time
            )
            return result
        except Exception as e:
            print_error(f"Error benchmarking {strategy_name}: {str(e)}")
            return None
    
    results = []
    
    if use_parallel:
        # Benchmark each strategy in parallel
        print_header("PARALLEL BENCHMARKING", "⚡")
        print(f"Benchmarking {len(strategy_names)} strategies in parallel...")
        
        with concurrent.futures.ProcessPoolExecutor() as executor:
            # Submit all benchmark tasks
            future_to_strategy = {
                executor.submit(benchmark_strategy, name): name 
                for name in strategy_names
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_strategy):
                strategy_name = future_to_strategy[future]
                try:
                    result = future.result()
                    if result is not None:
                        results.append(result)
                        print_check(f"{strategy_name} benchmark complete")
                        # Print individual results
                        print_optimization_stats({
                            "Strategy": strategy_name,
                            "Original execution time": f"{original_time:.4f} seconds",
                            "Optimized execution time": f"{result.optimized_time:.4f} seconds",
                            "Performance improvement": f"{result.improvement:.2f}%",
                            "Speedup factor": f"{result.speedup:.1f}×"
                        })
                except Exception as exc:
                    print_error(f"{strategy_name} benchmark failed: {exc}")
    else:
        # Benchmark each strategy sequentially
        print_header("SEQUENTIAL BENCHMARKING", "📊")
        print(f"Benchmarking {len(strategy_names)} strategies sequentially...")
        
        for strategy_name in strategy_names:
            try:
                result = benchmark_strategy(strategy_name)
                if result is not None:
                    results.append(result)
                    print_check(f"{strategy_name} benchmark complete")
                    # Print individual results
                    print_optimization_stats({
                        "Strategy": strategy_name,
                        "Original execution time": f"{original_time:.4f} seconds",
                        "Optimized execution time": f"{result.optimized_time:.4f} seconds",
                        "Performance improvement": f"{result.improvement:.2f}%",
                        "Speedup factor": f"{result.speedup:.1f}×"
                    })
            except Exception as e:
                print_error(f"Error benchmarking {strategy_name}: {str(e)}")
    
    # Save benchmark results
    if results:
        save_benchmark_results(results, base_dir)
        
        # Compare strategies
        print_header("STRATEGY COMPARISON", "🏆")
        # Sort by speedup
        results.sort(key=lambda x: x.optimized_time)
        
        for i, result in enumerate(results, 1):
            print(f"{i}. {result.strategy_name}: {result.speedup:.1f}× speedup ({result.improvement:.1f}% faster)")
        
        # Update active strategy to the fastest one
        with open("achilles_build", "w") as f:
            f.write(results[0].strategy_name)
        
        print(f"\nFastest strategy is {results[0].strategy_name} with {results[0].speedup:.1f}× speedup")
        print("This is now the active strategy when using 'achilles run'")
    else:
        print_error("No benchmarks were successfully run.")
        print_header("PROFILING ONLY", "🔍")
        with SpinnerContext("Analyzing code performance..."):
            benchmark = get_code_benchmark(args)
        print_check("Performance analysis complete")
        print("\nTop functions by execution time:")
        for i, func in enumerate(benchmark[:5], 1):
            print(f"  {i}. {func['func']} - {func['cumtime']:.4f}s ({func['ncalls']} calls)")
        print("\nRun 'achilles optimize' to improve performance of these functions.")
