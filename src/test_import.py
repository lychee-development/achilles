"""
Test script to verify if the achilles module can be imported
"""
import sys
import pkgutil

# Print Python path
print("Python path:")
for path in sys.path:
    print(f"  - {path}")

# List all installed packages
print("\nInstalled modules:")
for module in pkgutil.iter_modules():
    print(f"  - {module.name}")

# Try to import achilles
print("\nTrying to import achilles:")
try:
    import achilles
    print(f"Success! achilles found at: {achilles.__file__}")
    print(f"achilles.__name__: {achilles.__name__}")
    print(f"achilles.__package__: {achilles.__package__}")
except ImportError as e:
    print(f"Failed to import: {e}") 