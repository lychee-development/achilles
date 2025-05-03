import os
import ast
from achilles.data_models import UnoptimizedFunction

class FindFunctionVisitor(ast.NodeVisitor):
    """
    An AST visitor that finds a function definition node based on
    its name and starting line number.
    """
    def __init__(self, target_line: int, target_name: str):
        self.target_line = target_line
        self.target_name = target_name
        self.found_node: ast.FunctionDef | ast.AsyncFunctionDef | None = None

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # Check if the function definition starts at the target line
        # and has the target name.
        # Note: node.lineno points to the line where 'def' starts.
        if node.lineno == self.target_line and node.name == self.target_name:
            self.found_node = node
            # Stop visiting further nodes once found (optional optimization)
            return
        # Continue searching in nested functions/classes if needed
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        # Also handle async functions
        if node.lineno == self.target_line and node.name == self.target_name:
            self.found_node = node
            return
        self.generic_visit(node)

    # We might need to visit classes if the function is a method
    def visit_ClassDef(self, node: ast.ClassDef):
        # Continue searching within class definitions for methods
        self.generic_visit(node)


def get_function_code(f: UnoptimizedFunction) -> str:
    """
    Extracts the source code of a function using its path and line number.

    Args:
        f: An UnoptimizedFunction object containing path, line, and func name.

    Returns:
        The source code of the function as a string, including decorators,
        signature, docstring, and body. Returns an empty string or error message
        if the function cannot be found or the file cannot be read/parsed.
    """
    if not f.path or not os.path.exists(f.path):
        return f"# Error: File not found at path: {f.path}"

    try:
        # Read the source code file
        with open(f.path, 'r', encoding='utf-8') as source_file:
            source_code = source_file.read()
    except Exception as e:
        return f"# Error reading file {f.path}: {e}"

    try:
        # Parse the source code into an AST
        tree = ast.parse(source_code, filename=f.path)
    except SyntaxError as e:
        return f"# Error parsing file {f.path}: {e}"
    except Exception as e: # Catch other potential parsing errors
        return f"# Error during AST parsing of {f.path}: {e}"


    # Find the function node in the AST
    visitor = FindFunctionVisitor(target_line=f.line, target_name=f.func)
    try:
        visitor.visit(tree)
    except Exception as e:
        return f"# Error visiting AST for {f.func} in {f.path}: {e}"


    if visitor.found_node:
        try:
            # Use ast.get_source_segment (Python 3.8+) to extract the code
            # This correctly handles decorators, multiline signatures, etc.
            return ast.get_source_segment(source_code, visitor.found_node, padded=True)
        except Exception as e:
             return f"# Error extracting source segment for {f.func} at line {f.line} in {f.path}: {e}"
    else:
        # Function definition not found at the expected line/name
        # This could happen if the source code changed since profiling,
        # or if the profiling line number is slightly off (e.g., pointing
        # to a decorator instead of the 'def' line).
        # You might add more sophisticated searching logic here if needed.
        return f"# Error: Function '{f.func}' not found at line {f.line} in {f.path}"
