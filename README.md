# Pymortem: Advanced Python Debugging

<div align="center">

![PyPI](https://img.shields.io/pypi/v/pymortem)
![Python Versions](https://img.shields.io/pypi/pyversions/pymortem)
![License](https://img.shields.io/pypi/l/pymortem?logo=auto)
[![Codecov](https://codecov.io/gh/nsarang/pymortem/branch/main/graph/badge.svg)](https://codecov.io/gh/nsarang/pymortem)

</div>

Pymortem is a post-mortem debugging tool that lets you inspect and manipulate execution contexts after exceptions occur. Unlike traditional debuggers that require a separate interactive shell, pymortem gives you direct access to all variables and frames in the exception stack, making it valuable in Jupyter notebooks and interactive environments.

> This package evolved from an educational [blog post](https://nimasarang.com/blog/2025-01-30-post-mortem/) on post-mortem debugging techniques. What began as educational code examples has been refined into a practical debugging library.

## Installation

```bash
pip install pymortem
```

## Features

- **Enhanced Tracebacks**: Rich, visual traceback output showing code context around errors with line numbers and error indicators
- **Frame Inspection**: Directly examine variables at any level in the call stack without navigating through a separate command interface
- **Code Execution in Context**: Run arbitrary code in the context of any stack frame without restarting your program
- **Chained Exception Support**: Clear visualization of exception chains, showing both "raised from" and "during handling" relationships
- **No Special Setup**: Works with standard Python without requiring breakpoints or special execution modes

## Usage

### Examining an Exception after it Occurs

```python
# In one cell where an error happens:
def foo():
    x = 10
    output = x / 0
    return output

foo()
```

```python
# In the next cell, examine the exception:
import pymortem

# Get enhanced traceback and frame information
traceback_msg, frames = pymortem.extract_from_exception()

# Display the improved traceback
print(traceback_msg)
```

### Inspecting Variables in the Error Context

```python
# After running the above cells
# Let's examine the local variables in different frames

# The frame where the error occurred
print("Locals in error frame:", frames[-1]["locals"])

# Check global variables too
print("Some globals:", {k: v for k, v in list(frames[-1]["globals"].items())[:5]})
```

### Executing Code in a Frame's Context

```python
import pymortem
import sys

# Get the most recent exception
exception = pymortem.retrieve_the_last_exception() # Store the exception
_, frames = pymortem.extract_from_exception(exception)

# Choose a frame to work with (e.g., frames[1] for a specific frame)
work_frame = frames[-1]

# Execute code in that frame's context
pymortem.execute(
    """
    # You can access all variables that existed when the error occurred
    print("Available variables:", list(locals().keys()))

    # Test potential fixes without rerunning the entire notebook
    try:
        # Try a fix for a ZeroDivisionError
        denominator = 2  # Was 0 before
        fixed_result = x / denominator
        print(f"Fix worked! Result = {fixed_result}")
    except Exception as e:
        print(f"Fix didn't work: {e}")
    """,
    work_frame
)
```

### Handling Chained Exceptions

```python
# Create a chained exception scenario
try:
    try:
        x = {"key": "value"}
        result = x["missing_key"]  # Will raise KeyError
    except KeyError:
        result = 10 + "0"  # Will raise ValueError
except Exception as e:
    chain_exception = e

# Examine the exception chain
traceback_msg, all_frames = pymortem.extract_from_exception(chain_exception)
print(traceback_msg)
print("")

# Frames are arranged in chronological order, with the first exception first
original_error_frame = all_frames[0]  # Frame from the KeyError
raised_from_frame = all_frames[-1]    # Frame from the ValueError

print(f"First exception type: {type(chain_exception.__cause__)}")
print(f"Second exception type: {type(chain_exception)}")
```

## Why Use Pymortem?

Post-mortem debugging in Python traditionally requires using tools like `pdb.pm()` or `%debug` in IPython, which launch a separate command interface with its own syntax and navigation model. Pymortem takes a different approach:

1. **Direct Context Access**: Instead of a separate debugging shell, access frame data directly in your current Python environment
2. **Better Visualization**: See more context around exceptions with cleaner, more informative tracebacks
3. **Natural Code Execution**: Run diagnostic code directly in frame contexts using standard Python syntax
4. **Stays in Flow**: Particularly valuable in notebooks where switching to a separate debugging interface breaks your workflow
5. **Handles Complexity**: Elegantly deals with nested and chained exceptions that can be confusing in traditional debuggers

## License

MIT
