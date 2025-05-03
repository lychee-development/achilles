
import random
import time
import argparse

def fib(n):
    """Naïve recursive Fibonacci (exponential time)."""
    if n < 2:
        return n
    return fib(n-1) + fib(n-2)

def string_concat(n):
    """Quadratic-time string concatenation."""
    s = ""
    for _ in range(n):
        s += "x"
    return s

def sort_random_list(size):
    """Generate and sort a list of random floats."""
    lst = [random.random() for _ in range(size)]
    lst.sort()
    return lst

def cpu_loop(iterations):
    """Simple arithmetic loop."""
    total = 0
    for i in range(iterations):
        total += i * i
    return total

def main(fib_n, size, iters):
    print(f"Computing fib({fib_n})…")
    start = time.time()
    print(f"  Result: {fib(fib_n)}")
    print(f"  Time:   {time.time() - start:.3f}s\n")

    print(f"Concatenating string {size} times…")
    start = time.time()
    string_concat(size)
    print(f"  Time: {time.time() - start:.3f}s\n")

    print(f"Sorting random list of size {size}…")
    start = time.time()
    sort_random_list(size)
    print(f"  Time: {time.time() - start:.3f}s\n")

    print(f"Running cpu_loop({iters}) iterations…")
    start = time.time()
    cpu_loop(iters)
    print(f"  Time: {time.time() - start:.3f}s")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test script for cProfile")
    parser.add_argument("--fib-n",  type=int, default=30,
                        help="n for fib()")
    parser.add_argument("--size",   type=int, default=5000000,
                        help="size for string_concat and sort_random_list")
    parser.add_argument("--iters",  type=int, default=3000000,
                        help="iterations for cpu_loop")
    args = parser.parse_args()
    main(args.fib_n, args.size, args.iters)
