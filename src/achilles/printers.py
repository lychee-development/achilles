"""
Printers module for Achilles CLI.

This module provides fancy terminal output formatting for the Achilles CLI,
including box headers, spinners, status indicators, and more.
"""

import time
import threading
from rich.console import Console
from rich.panel import Panel
from rich.spinner import Spinner
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich import print as rprint

# Initialize console
console = Console()

def print_header(title, emoji):
    """Print a boxed header with emoji."""
    console.print()
    console.print(Panel(f"{emoji} {title}", border_style="white", width=55))

def print_check(message):
    """Print a checkmark with message."""
    console.print(f"[green]✓[/green] {message}")

def print_warning(message):
    """Print a warning with message."""
    console.print(f"[yellow]![/yellow] {message}")

def print_error(message):
    """Print an error with message."""
    console.print(f"[red]✗[/red] {message}")

def print_detail(message, indent=6):
    """Print an indented detail line."""
    console.print(" " * indent + f"[dim]↳[/dim] {message}")

class SpinnerContext:
    """Context manager for spinner animation."""
    def __init__(self, message, index=None, total=None):
        self.message = message
        self.index = index
        self.total = total
        self.spinner_chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        self.spinner_idx = 0
        self.thread = None
        self.running = False
        self.progress = None
        self.task_id = None
        
    def __enter__(self):
        prefix = f"[{self.index}/{self.total}] " if self.index and self.total else ""
        
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn(f"{prefix}{self.message}"),
            transient=True
        )
        
        self.live = Live(self.progress, refresh_per_second=10)
        self.live.start()
        self.task_id = self.progress.add_task("", total=None)
        
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.live.stop()
        # Clear the line and add a newline to ensure proper spacing
        console.print("\r" + " " * 80 + "\r", end="")
        # Force a newline after spinner completes to fix spacing issues
        console.print("")

def print_optimization_complete(speedup):
    """Print optimization complete message with speedup."""
    console.print(f"\n[green]✅ Optimization complete![/green] ([bold]{speedup}×[/bold] faster)")

def print_optimization_failed(reason):
    """Print optimization failed message with reason."""
    console.print(f"\n[red]❌ Optimization failed:[/red] {reason}")

def print_optimization_stats(stats):
    """Print optimization statistics."""
    console.print("\n[bold]Optimization Statistics:[/bold]")
    for key, value in stats.items():
        console.print(f"  [dim]•[/dim] {key}: {value}")

def print_help():
    """Print the main help message with fancy formatting."""
    console.print("""
╭───────────────────────────────────────────────╮
│                   ACHILLES                    │
│        Python Performance Optimizer           │
╰───────────────────────────────────────────────╯

COMMANDS:
  [bold]optimize[/bold]    Analyze and optimize Python code
  [bold]benchmark[/bold]   Compare optimized vs original code
  [bold]run[/bold]         Execute optimized Python code
  [bold]inspect[/bold]     Detailed performance insights
  [bold]config[/bold]      Configure optimization settings

Get started with: [bold]achilles optimize your_script.py[/bold]
""")

# Simple spinner for when you don't need a context manager
def start_spinner(message):
    """Start a spinner with a message and return the spinner object."""
    progress = Progress(
        SpinnerColumn(),
        TextColumn(message),
        transient=True
    )
    live = Live(progress, refresh_per_second=10)
    live.start()
    task_id = progress.add_task("", total=None)
    return (live, progress, task_id)

def stop_spinner(spinner_tuple):
    """Stop a spinner created with start_spinner."""
    live, progress, task_id = spinner_tuple
    live.stop()
    # Clear the line
    console.print("\r" + " " * 80 + "\r", end="")
