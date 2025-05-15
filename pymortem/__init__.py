"""
Pymortem - Advanced Python Post-mortem Debugging Tools
======================================================

This package provides utilities for post-mortem debugging in Python,
allowing inspection and manipulation of execution contexts after crashes.
"""

__version__ = "1.0.1"

from .core import (
    execute,
    extract_from_exception,
    get_chained_exceptions,
    process_single_exception,
    retrieve_the_last_exception,
)

__all__ = [
    "__version__",
    "execute",
    "extract_from_exception",
    "get_chained_exceptions",
    "process_single_exception",
    "retrieve_the_last_exception",
]
