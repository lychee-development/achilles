import sys
import os

# Handle both direct execution and module import
from achilles.achilles import optimize, benchmark, run
from achilles.printers import print_help, print_error
from achilles.strategies import get_available_strategies, get_strategy

def print_usage():
    """Print command usage information."""
    print("Usage: achilles [command] your_python_file.py [--your_python_args]")
    print("\nCommands:")
    print("  optimize    Optimize Python code with multiple strategies and auto-benchmark")
    print("    --no-parallel  Disable parallel optimization (run strategies sequentially)")
    print("  benchmark   Compare performance between all optimized strategies")
    print("    --no-parallel  Disable parallel benchmarking (run strategies sequentially)")
    print("  run         Run Python code with the fastest optimized strategy")
    print("  list-strategies  List all available optimization strategies")
    print("\nExamples:")
    print("  achilles optimize script.py --arg1 value1")
    print("  achilles optimize --no-parallel script.py")
    print("  achilles benchmark script.py")
    print("  achilles run script.py --input data.csv")
    print("  achilles list-strategies")

def main():
    # Note: sys.argv[0] is the name of this script (cli.py)
    # Command should be at position 1, and user's script at position 2
    args = sys.argv[1:]
    
    if not args or args[0] in ("--help", "-h"):
        print_help()
        sys.exit(0)
    
    command = args[0]
    script_args = args[1:]  # The Python file and its arguments
    
    if command in ("optimize", "benchmark", "run"):
        # Process flags
        use_parallel = True
        if "--no-parallel" in script_args:
            use_parallel = False
            script_args.remove("--no-parallel")
        
        if not script_args:
            print_error("Missing Python file to process.")
            print_usage()
            sys.exit(1)
        
        if command == "optimize":
            optimize(script_args, use_parallel=use_parallel)
        elif command == "benchmark":
            benchmark(script_args, use_parallel=use_parallel)
        elif command == "run":
            run(script_args)
    elif command == "list-strategies":
        print("Available optimization strategies:")
        for name in get_available_strategies():
            strategy = get_strategy(name)
            print(f"  - {name}: {strategy.description}")
        sys.exit(0)
    else:
        print_error(f"Unknown command: {command}")
        print_usage()
        sys.exit(1)

if __name__ == ("__main__"):
    main()
