import pstats, sysconfig, subprocess, os, sys
from pathlib import Path

def profile_via_subprocess(run_string, output_file="profile.prof"):
    # split into ["myscript.py", "--foo", "bar"]
    # invoke: python -m cProfile -o profile.prof myscript.py --foo bar
    cmd = [sys.executable, "-m", "cProfile", "-o", output_file] + run_string
    subprocess.run(cmd, check=True)

    # load and inspect
    stats = pstats.Stats(output_file).strip_dirs()
    return stats

paths = sysconfig.get_paths()
EXCLUDE_DIRS = {
    os.path.abspath(paths["stdlib"]),
    os.path.abspath(paths["platstdlib"]),
    os.path.abspath(paths["purelib"]),
    os.path.abspath(paths["platlib"]),
}

def top_n_funcs(stats, n=10, min_cumtime=0.0, exclude_dirs=EXCLUDE_DIRS):
    """
    Returns a list of the top‐n user‐defined functions sorted by descending cumtime.
    Each entry is a dict with keys: file, line, func, ncalls, tottime, cumtime.
    """
    rows = []
    for func, (cc, nc, tt, ct, callers) in stats.stats.items():
        filename, lineno, funcname = func

        # skip builtins
        if filename in ("<built-in>", None):
            continue
        fn = Path(filename).resolve()
        # skip stdlib / site-packages
        if any(fn.is_relative_to(d) for d in exclude_dirs):
            continue
        # skip tiny timings
        if ct < min_cumtime:
            continue

        rows.append({
            "file": str(fn),
            "line": lineno,
            "func": funcname,
            "ncalls": nc,
            "tottime": tt,
            "cumtime": ct,
        })

    # sort descending by cumtime and take top n
    rows.sort(key=lambda r: r["cumtime"], reverse=True)
    return rows[:n]

# This function links the other two together. In the future, we can add more filters to this function regarding the cprofile output.
def get_code_benchmark(args, min_cumtime=0.001):
    stats = profile_via_subprocess(args)
    top_n = top_n_funcs(stats, min_cumtime=min_cumtime)
    # Remove the print statement that's showing raw data
    return top_n
if __name__ == "__main__":
    print(get_code_benchmark(sys.argv[1:]))
