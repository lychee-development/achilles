import anthropic
from achilles.data_models import UnoptimizedFunction
import json
import os
import re
from achilles.file_ops.function_ops import get_function_code
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYS_PROMPT = """
You are an expert at analyzing performance of python code. Provided to you is a record of function calls, and the time they took.
You have the ability to read the python code associated with these function calls via a tool call. Your job is to output a list
of function call ids associated with functions that you believe should be rewritten in C++ to improve performance.

WORKFLOW (YOU MUST FOLLOW THIS EXACTLY):
1. First, use the read_function_code tool for EACH user-defined function (one at a time)
2. Only after reading ALL user-defined functions, perform your analysis
3. Provide your reasoning about each function's suitability for C++ optimization
4. End your response with a JSON array of function IDs you recommend

When selecting functions for C++ optimization, prioritize these criteria, but remember they need not all be met:
1. High number of calls (ncalls) - functions called frequently are prime candidates
2. High cumulative time (cum_time > 0.002) - functions that consume significant execution time
3. Functions with CPU-intensive operations like mathematical calculations, loops, string manipulations
4. Functions that don't heavily depend on Python-specific libraries or features

Specifically:
- Focus on user-defined functions (those not marked with built-in, method, or in system paths)
- Prioritize functions with computational loops, numerical processing, or data manipulation
- Functions with many calls and high cumulative time should be your top candidates
- Simpler algorithmic functions are easier to port to C++ than complex ones with many dependencies

You can provide your analysis and reasoning, then conclude with your final answer.

CRUCIAL: Your final output MUST end with a JSON array of integers representing the function IDs you selected, such as:
[1, 2, 6, 9, 13]

If no functions should be optimized, explain why each function cannot be optimized and respond with an empty array: []
"""

def extract_list_from_text(text):
    """Attempts to extract a list of integers from text using various methods."""
    # First, try direct JSON parsing
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass
    
    # Try to find a list pattern with regex
    list_pattern = r'\[\s*(?:\d+\s*,\s*)*\d*\s*\]'
    match = re.search(list_pattern, text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    
    # If no list is found or it can't be parsed
    return []

def select_functions(functions: list[dict]) -> list[UnoptimizedFunction]:
    # Convert dictionary to UnoptimizedFunction objects
    converted_functions = [
        UnoptimizedFunction(
            path=fn["file"], 
            line=fn["line"], 
            func=fn["func"], 
            calls=fn["ncalls"], 
            cum_time=fn["cumtime"]
        ) for fn in functions
    ]
    
    # 1) index your functions
    functions_indexed = {i: fn for i, fn in enumerate(converted_functions)}

    # 2) prepare the LLM messages
    func_summaries = [
        {
            "id": idx,
            "path": fn.path,
            "line": fn.line,
            "name": fn.func,
            "calls": fn.calls,
            "cum_time": fn.cum_time,
            "is_user_defined": not (fn.func.startswith('<') or '/~' in fn.path or '<frozen' in fn.path)
        }
        for idx, fn in functions_indexed.items()
    ]

    user_content = "Here are the functions available for optimization:\n" + json.dumps(func_summaries, indent=2) + "\n\nIMPORTANT: You MUST use the read_function_code tool for EACH user-defined function (is_user_defined=true) before deciding which to optimize. After analyzing each function, conclude with a JSON array of function IDs you recommend for optimization."
    
    # Initialize messages array for the conversation
    messages = [
        {"role": "user", "content": user_content}
    ]
    
    # 3) loop until Claude gives you a final answer
    while True:
        resp = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=4096,
            system=SYS_PROMPT,
            messages=messages,
            tools=[{
                "type": "custom",
                "name": "read_function_code",
                "description": "REQUIRED: Use this tool to read the code for each user-defined function.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "func_id": {
                            "type": "integer",
                            "description": "The ID of the function to read"
                        }
                    },
                    "required": ["func_id"]
                }
            }],
        )

        # 4) if it's a tool invocation…
        if resp.stop_reason == "tool_use":
            # Get the content block with the tool use
            tool_use_block = next((block for block in resp.content if block.type == "tool_use"), None)
            
            if tool_use_block:
                func_id = tool_use_block.input["func_id"]
                print(f"Tool use: reading function {func_id}: {functions_indexed[func_id].func}")
                code = get_function_code(functions_indexed[func_id])
                
                # Add assistant's tool use message
                messages.append({
                    "role": "assistant", 
                    "content": [{
                        "type": "tool_use",
                        "name": tool_use_block.name,
                        "input": tool_use_block.input,
                        "id": tool_use_block.id
                    }]
                })
                
                # Add tool response
                messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": tool_use_block.id,
                        "content": code
                    }]
                })
                
                # and loop to let Claude continue
                continue

        # 5) otherwise it's the final answer
        text_block = next((block for block in resp.content if block.type == "text"), None)
        final = text_block.text if text_block else ""
        break

    # 6) parse the list of indices, and map back using a more robust method
    selected_ids = extract_list_from_text(final)
    print(f"Selected IDs: {selected_ids}")
    
    if not selected_ids and "[]" not in final:
        # print("WARNING: The model did not return a proper JSON array. Check the model response for errors.")
        # print("Consider increasing max_tokens or adjusting the prompt to ensure the model follows instructions.")
        pass

    return [functions_indexed[i] for i in selected_ids if i in functions_indexed]
