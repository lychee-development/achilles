import os
import json
import subprocess
import sys
import importlib
import importlib.util
import hashlib
from typing import Optional
from achilles.strategies import get_strategy, get_fastest_strategy

class UnoptimizedFunction:
    def __init__(self, path, line, func, calls, cum_time):
        self.path = path
        self.line = line
        self.func = func
        self.calls = calls
        self.cum_time = cum_time

class OptimizedFunction:
    def __init__(self,
                 unoptimized_func: UnoptimizedFunction,
                 cpp_code: str,
                 cpp_func_name: str, # Name of the C++ function implementing the logic
                 pybind_module_name: str, # Name of the Pybind11 module (e.g., "_achilles_optimized_funcs")
                 pybind_exposed_name: str # Name under which the function is exposed in the module (usually same as original Python func name)
                 ):
        self.unoptimized_func = unoptimized_func
        self.cpp_code = cpp_code # The generated C++ source code snippet for this function
        self.cpp_func_name = cpp_func_name
        self.pybind_module_name = pybind_module_name
        self.pybind_exposed_name = pybind_exposed_name

def build_cpp_modules(optimized_functions: list[OptimizedFunction], strategy_name: str = "standard"):
    """Build C++ modules for a specific strategy"""
    
    strategy = get_strategy(strategy_name)
    
    # Get absolute paths
    base_dir = os.path.abspath(os.getcwd())
    strategy_dir = os.path.join(base_dir, ".achilles", "strategies", strategy_name)
    src_dir = os.path.join(strategy_dir, "src")
    
    # Clean up any previous build for this strategy
    if os.path.exists(src_dir):
        subprocess.run(["rm", "-rf", src_dir], check=False)
    
    # Create directory structure
    os.makedirs(src_dir, exist_ok=True)
    os.makedirs(os.path.join(strategy_dir, "build"), exist_ok=True)
    
    # Use strategy-specific module name to avoid collisions
    module_name = f"_achilles_optimized_{strategy.name}"
    
    # Extract function implementations and create a unified module
    implementations = []
    bindings = []
    
    for i, opt_func in enumerate(optimized_functions):
        # Generate a modified version of the C++ code without pybind11 module init
        stripped_code = extract_implementation(opt_func.cpp_code, opt_func.cpp_func_name)
        
        # Save the stripped implementation to a header file
        header_file = os.path.join(src_dir, f"{opt_func.unoptimized_func.func}_{i}.h")
        with open(header_file, "w") as f:
            f.write(stripped_code)
        
        implementations.append(f'#include "{os.path.basename(header_file)}"')
        bindings.append(f'm.def("{opt_func.pybind_exposed_name}", &{opt_func.cpp_func_name}, "Optimized version of {opt_func.unoptimized_func.func}");')
    
    # Create a unified module file specific to this strategy
    module_file = os.path.join(src_dir, "module.cpp")
    module_code = f"""
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <vector>
#include <string>

namespace py = pybind11;

// Include function implementations
{chr(10).join(implementations)}

PYBIND11_MODULE({module_name}, m) {{
    // Add function bindings
    {chr(10)    .join(bindings)}
}}
"""
    
    with open(module_file, "w") as f:
        f.write(module_code)
    
    # Store metadata for runtime patching
    metadata = {}
    for opt_func in optimized_functions:
        metadata[opt_func.unoptimized_func.func] = {
            "module": module_name,
            "exposed_name": opt_func.pybind_exposed_name,
            "original_path": opt_func.unoptimized_func.path,
            "original_line": opt_func.unoptimized_func.line
        }
    
    # Write metadata.json for this strategy
    with open(os.path.join(strategy_dir, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)
    
    # Generate setup.py for compiling
    generate_setup_py([module_file], strategy_dir)
    
    # Generate pyproject.toml in strategy directory
    generate_pyproject_toml(strategy_dir)
    
    # Keep a simplified version of the file listing that's more user-friendly
    print(f"Files in {strategy_name} src directory:")
    for file in os.listdir(src_dir):
        file_path = os.path.join(src_dir, file)
        print(f"  - {os.path.basename(file_path)} (exists: {os.path.exists(file_path)})")
    
    # Compile using uv instead of pip
    try:
        subprocess.check_call(["uv", "pip", "install", "-e", strategy_dir])
    except subprocess.CalledProcessError:
        print(f"Error: Failed to install C++ extension for {strategy_name} with uv.")
        print("Make sure pybind11 is installed. Try running: uv pip install pybind11")
        raise
    
    # Create strategy marker file
    with open(os.path.join(strategy_dir, "achilles_build"), "w") as f:
        f.write(strategy_name)
    
    # Create link to the active strategy in the base dir
    with open(os.path.join(base_dir, "achilles_build"), "w") as f:
        f.write(strategy_name)

def extract_implementation(cpp_code, func_name):
    """Extract just the function implementation from the C++ code, removing pybind11 module parts."""
    # Basic parsing to extract just the function implementation
    lines = cpp_code.split('\n')
    implementation_lines = []
    in_function = False
    skip_module = False
    
    for line in lines:
        # Skip pybind11 module definition lines
        if "PYBIND11_MODULE" in line:
            skip_module = True
            continue
        
        if skip_module:
            if line.strip() == "}":
                skip_module = False
            continue
        
        # Include all non-module lines (imports, function definitions, etc.)
        if not skip_module:
            implementation_lines.append(line)
    
    return "\n".join(implementation_lines)

def generate_pyproject_toml(achilles_dir):
    content = """
[build-system]
requires = ["setuptools>=42", "pybind11>=2.10.0"]
build-backend = "setuptools.build_meta"
"""
    with open(os.path.join(achilles_dir, "pyproject.toml"), "w") as f:
        f.write(content)

def generate_setup_py(cpp_files, achilles_dir):
    # Extract strategy name from directory path
    strategy_name = os.path.basename(achilles_dir.rstrip('/'))
    module_name = f"_achilles_optimized_{strategy_name}"
    
    setup_content = """
from setuptools import setup, Extension
import pybind11
import os
import subprocess
import sys

# Verify files exist before compilation
sources = [
    {sources}
]
for source in sources:
    if not os.path.exists(source):
        raise ValueError(f"Source file not found: {{source}}")

# Get the correct SDK path on macOS
extra_compile_args = ['-std=c++14', '-O3']
extra_link_args = []

if sys.platform == 'darwin':
    try:
        # Find the correct SDK path
        sdk_path = subprocess.check_output(['xcrun', '--show-sdk-path'], text=True).strip()
        if sdk_path:
            print(f"Using SDK path: {{sdk_path}}")
            extra_compile_args.extend(['-isysroot', sdk_path])
            extra_link_args.extend(['-isysroot', sdk_path])
        
        # Add explicit linkage to libc++
        extra_link_args.append('-stdlib=libc++')
    except Exception as e:
        print(f"Warning: Failed to get SDK path: {{e}}")

ext_modules = [
    Extension(
        '{module_name}',
        sources=sources,
        include_dirs=[pybind11.get_include(), os.path.dirname(sources[0])],  # Include src directory
        language='c++',
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
    ),
]

setup(
    name='achilles_optimized_{strategy_name}',
    ext_modules=ext_modules,
)
"""
    # Format the sources list and replace template parameters
    sources_str = ",\n            ".join([f"'{f}'" for f in cpp_files])
    setup_content = setup_content.replace("{sources}", sources_str)
    setup_content = setup_content.replace("{module_name}", module_name)
    setup_content = setup_content.replace("{strategy_name}", strategy_name)
    
    with open(os.path.join(achilles_dir, "setup.py"), "w") as f:
        f.write(setup_content)

def apply_optimizations(strategy_name: Optional[str] = None):
    """
    Apply optimizations from the specified strategy, or the best strategy if not specified.
    """
    
    base_dir = os.path.abspath(os.getcwd())
    
    # Determine which strategy to use
    if not strategy_name:
        # Check for active strategy in achilles_build
        if os.path.exists(os.path.join(base_dir, "achilles_build")):
            with open(os.path.join(base_dir, "achilles_build"), "r") as f:
                strategy_name = f.read().strip()
        else:
            # Use fastest if available
            fastest = get_fastest_strategy(base_dir)
            strategy_name = fastest if fastest else "standard"
    
    # Get the strategy directory
    strategy_dir = os.path.join(base_dir, ".achilles", "strategies", strategy_name)
    
    if not os.path.exists(os.path.join(strategy_dir, "achilles_build")):
        print(f"Strategy '{strategy_name}' has not been built.")
        return False
    
    # Load metadata specific to this strategy
    metadata_path = os.path.join(strategy_dir, "metadata.json")
    if not os.path.exists(metadata_path):
        print(f"Metadata for strategy '{strategy_name}' not found.")
        return False
        
    with open(metadata_path, "r") as f:
        metadata = json.load(f)
    
    # Import the strategy-specific optimized module
    module_name = f"_achilles_optimized_{strategy_name}"
    try:
        optimized_module = importlib.import_module(module_name)
    except ImportError:
        print(f"Failed to import optimized functions for strategy '{strategy_name}'. Rebuild may be required.")
        return False
    
    # Apply monkey patching
    patch_count = 0
    for func_name, func_info in metadata.items():
        # Find the module containing the original function
        try:
            # Load the module from file path
            module_path = func_info["original_path"]
            spec = importlib.util.spec_from_file_location("target_module", module_path)
            target_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(target_module)
            
            # Replace the original function with optimized version
            optimized_func = getattr(optimized_module, func_info["exposed_name"])
            setattr(target_module, func_name, optimized_func)
            patch_count += 1
        except Exception as e:
            print(f"Failed to patch function {func_name}: {e}")
    
    print(f"Successfully applied {patch_count} optimizations from strategy '{strategy_name}'")
    return True
