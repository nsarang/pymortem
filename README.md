# Pymortem: Advanced Python Debugging

![PyPI](https://img.shields.io/pypi/v/pymortem)
![Python Versions](https://img.shields.io/pypi/pyversions/pymortem)
![License](https://img.shields.io/pypi/l/pymortem)

A bit of Python black magic that lets you efficiently inspect and manipulate execution contexts after crashes, aka, post-mortem debugging.

## Installation

```bash
pip install pymortem
```

## Features

- Improved exception tracebacks with more context
- Inspect local and global variables at each frame in the exception stack
- Handle chained exceptions elegantly
- Execute code within the context of any frame in the stack
- Works in both scripts and interactive environments (including Jupyter notebooks)

## Usage

### Basic Exception Analysis

```python
import pymortem

try:
    # Your code that might raise an exception
    result = 1 / 0
except Exception as e:
    # Get a better traceback with surrounding context
    traceback_message, frame_info = pymortem.extract_from_exception(e)
    print(traceback_message)

    # Inspect variables at a specific frame
    print(frame_info[0]["locals"])  # Local variables at the first frame
```

### Executing Code in Exception Context

```python
import pymortem

# After an exception occurs
exception = sys.last_value  # Get the last exception
_, frame_info = pymortem.extract_from_exception(exception)

# Execute code in the context of a specific frame
pymortem.execute("""
print("Variables in this context:", locals().keys())
# Fix or inspect variables
result = some_variable * 2
print("Modified result:", result)
""", frame_info[1])  # Using frame 1 as an example
```

## Why Use Pymortem?

Traditional debugging with `pdb` can be cumbersome, especially in larger projects or when using Jupyter notebooks. Pymortem gives you:

1. Better traceback visualization with surrounding code context
2. Direct access to variables at each step of the stack without navigating through a separate UI
3. Ability to execute arbitrary code within any frame's context
4. Support for both nested exceptions and IPython/Jupyter environments

## License

MIT
