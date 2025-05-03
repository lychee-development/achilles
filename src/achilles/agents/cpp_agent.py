from achilles.file_ops.function_ops import get_function_code
from achilles.data_models import UnoptimizedFunction, OptimizedFunction
import anthropic
import os
import json
import re
from dotenv import load_dotenv
from achilles.strategies import get_strategy

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

PYBIND_MODULE_NAME = "_achilles_optimized_funcs"
MODEL_NAME = "claude-3-7-sonnet-20250219"  # Updated to use the latest Claude model
CPP_GENERATION_SYS_PROMPT = f"""
You are an expert C++ programmer specializing in performance optimization and interfacing C++ with Python using Pybind11.
Your task is to convert the provided Python function into an equivalent C++ function and create the necessary Pybind11 bindings to expose it back to Python.

**Input:** You will receive the source code of a Python function.

**Output:** You MUST provide your response as a single JSON object containing the following keys:
- "cpp_code": A string containing the complete C++ code. This code should include:
    - Necessary C++ standard library headers (e.g., `<vector>`, `<string>`, `<map>`, `<stdexcept>`).
    - The C++ function implementing the core logic. Use standard C++ types (int, double, std::string, std::vector, std::map, etc.) corresponding to Python types. Handle potential type errors gracefully if possible, or document assumptions.
    - The Pybind11 module definition boilerplate (`#include <pybind11/pybind11.h>`, `#include <pybind11/stl.h>` for standard containers, `namespace py = pybind11;`, `PYBIND11_MODULE(...)`).
    - Inside the `PYBIND11_MODULE({PYBIND_MODULE_NAME}, m)`, include the `m.def(...)` call to expose your C++ function.
- "cpp_func_name": The exact name of the generated C++ *logic* function (not the Pybind11 module name or exposed name).
- "pybind_exposed_name": The name under which the function should be exposed in the Python module. This should generally match the original Python function name.

**Constraints & Guidelines:**
- The generated C++ code must be self-contained and compilable for the given function.
- Assume standard C++11 or later.
- Use `pybind11::object` or specific types like `pybind11::list`, `pybind11::dict` if needed for complex interactions, but prefer standard C++ types for the core logic function signature where possible for clarity and potential performance benefits. Use `#include <pybind11/stl.h>` to enable automatic conversions for standard containers like `std::vector`, `std::map`, `std::string`.
- Aim for functionally equivalent C++ code. Optimize for performance where appropriate (e.g., prefer `std::vector` over Python lists for numerical operations).
- Do NOT include a `main` function in the C++ code.
- The Pybind11 module name MUST be `{PYBIND_MODULE_NAME}`.
- Ensure the JSON output is valid. Do not include any text outside the JSON object.
"""

CPP_GENERATION_USER_PROMPT_TEMPLATE = """
Please convert the following Python function into C++ with Pybind11 bindings, following the instructions provided in the system prompt.

Python Function Name: `{func_name}`
Python Function Source Code:
```python
{python_code}
```

Generate the JSON output containing "cpp_code", "cpp_func_name", and "pybind_exposed_name".
"""

def _clean_json_response(raw_response: str) -> str:
    """Attempts to extract a JSON object from the LLM response."""
    # Comment out debug prints to keep the output clean
    # print(f"Raw response length: {len(raw_response)}")
    # print(f"Raw response starts with: {raw_response[:100]}...")
    
    # Find the first '{' and the last '}'
    start = raw_response.find('{')
    end = raw_response.rfind('}')
    if start != -1 and end != -1 and end > start:
        return raw_response[start:end+1]
    
    # Fallback: try removing markdown code fences
    cleaned = re.sub(r"```json\n?|\n?```", "", raw_response.strip())
    if cleaned.startswith('{') and cleaned.endswith('}'):
        return cleaned
    
    # Last resort: create a minimal valid JSON with defaults
    print("WARNING: Could not extract valid JSON from response. Using default values.")
    return '{"cpp_code": "// Error extracting code", "cpp_func_name": "error_func", "pybind_exposed_name": "error_func"}'

def optimize_functions(functions: list[UnoptimizedFunction], strategy_name: str = "standard") -> list[OptimizedFunction]:
    """
    Generates C++ versions of Python functions using an LLM and Pybind11.

    Args:
        functions: A list of UnoptimizedFunction objects selected for optimization.
        strategy_name: The name of the optimization strategy to use.

    Returns:
        A list of OptimizedFunction objects containing the generated C++ code
        and metadata. Returns an empty list if no functions are provided or
        if errors occur during generation for all functions.
    """
    
    optimized_functions: list[OptimizedFunction] = []
    
    if not functions:
        return optimized_functions
    
    # Load the strategy
    strategy = get_strategy(strategy_name)
    
    # Use the strategy's module name
    module_name = f"_achilles_optimized_{strategy.name}"
    
    print(f"Using optimization strategy: {strategy.name}")
    print(f"Description: {strategy.description}")
    
    for unopt_func in functions:
        # 1. Get Python function code
        python_code = get_function_code(unopt_func)

        # 2. Prepare LLM messages with strategy-specific prompt
        user_prompt = CPP_GENERATION_USER_PROMPT_TEMPLATE.format(
            func_name=unopt_func.func,
            python_code=python_code
        )

        # 3. Call Anthropic API with strategy-specific settings
        response = client.messages.create(
            model=strategy.model,
            max_tokens=4096,
            system=strategy.prompt_template,  # Use strategy-specific prompt
            messages=[
                {"role": "user", "content": user_prompt}
            ],
            temperature=strategy.parameters.get("temperature", 0.2),
        )

        raw_response_content = response.content[0].text

        # 4. Parse the JSON response
        cleaned_response = _clean_json_response(raw_response_content)
        result_data = json.loads(cleaned_response)

        # 5. Create OptimizedFunction object with strategy-specific module name
        optimized_func = OptimizedFunction(
            unoptimized_func=unopt_func,
            cpp_code=result_data["cpp_code"],
            cpp_func_name=result_data["cpp_func_name"],
            pybind_module_name=module_name,  # Use strategy-specific module name
            pybind_exposed_name=result_data["pybind_exposed_name"]
        )

        optimized_functions.append(optimized_func)

    return optimized_functions
