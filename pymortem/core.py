import inspect
import sys
import textwrap
from typing import Dict, List, Tuple


def process_single_exception(
    exception: Exception,
    context_lines: int = 1,
    max_indent: int = float("inf"),
    frame_index: int = 0,
) -> Tuple[str, List[Dict]]:
    """
    Process an exception and return a formatted traceback message with frame information.

    Iterates through the traceback frames of an exception, formats each frame with
    code context, and collects both a human-readable message and detailed frame data.

    Parameters
    ----------
    exception : Exception
        The exception object to process and format.
    context_lines : int, default 1
        Number of source code lines to include around the error line for context.
        Must be >= 1.
    max_indent : int, default float("inf")
        Maximum indentation level preserved in displayed code. Code with greater
        indentation will be reformatted to this level. Use to prevent excessive
        indentation in deeply nested code.
    frame_index : int, default 0
        Starting index for frame numbering. Useful when combining multiple tracebacks.

    Returns
    -------
    traceback_message : str
        Formatted human-readable traceback message with frame information and code context.
    frame_info : List[Dict]
        List of dictionaries containing detailed information about each frame:
        - message: str, formatted frame message
        - frame: frame object
        - locals: dict, local variables at the frame
        - globals: dict, global variables at the frame
        - metadata: dict with frame details (filename, line number, function name, etc.)
    """
    tb = exception.__traceback__
    frame_info = []

    while tb is not None:
        # Get high-level frame information
        filename, lineno, function_name, lines, index = inspect.getframeinfo(
            tb, context=context_lines
        )

        # Dedent the lines if the entire block is indented more than max_indent
        lines_dedented = textwrap.dedent("".join(lines)).splitlines()
        if lines_dedented and lines[0] and len(lines[0]) - len(lines_dedented[0]) > max_indent:
            lines = textwrap.indent("\n".join(lines_dedented), " " * max_indent).splitlines()

        # Construct the frame message
        start_no = lineno - index
        end_no = lineno + len(lines) - index
        number_width = len(str(end_no))

        frame_message = [
            f"┌─── Frame {frame_index} " + "─" * 40,
            f'Function {function_name}, in file "{filename}"',
        ]

        for i, file_lineno in enumerate(range(start_no, end_no)):
            line = lines[i].rstrip() if i < len(lines) else ""
            prefix = "➤➤➤ " if i == index else "    "
            frame_message.append(f" {prefix}{file_lineno:{number_width}}:  {line}")

        frame_message.append("")

        frame_info.append(
            {
                "message": "\n".join(frame_message),
                "frame": tb.tb_frame,
                "locals": tb.tb_frame.f_locals.copy(),  # shallow copy just in case
                "globals": tb.tb_frame.f_globals.copy(),
                "metadata": {
                    "filename": filename,
                    "lineno": lineno,
                    "function_name": function_name,
                    "lines": lines if lines else [],
                    "index": index,
                },
            }
        )

        tb = tb.tb_next
        frame_index += 1

    exception_header = f"{type(exception).__name__}: {exception!s}"
    traceback_message = " \n".join([frame["message"] for frame in frame_info] + [exception_header])
    return traceback_message, frame_info


def get_chained_exceptions(exc: Exception) -> List[Tuple[Exception, str]]:
    """
    Extract a list of chained exceptions from an exception object.

    Parameters
    ----------
    exc : Exception
        The exception object to process.

    Returns
    -------
    List[Tuple[Exception, str]]
        List of tuples containing (exception, reason) pairs in order of occurrence.
        The reason will be either "__cause__", "__context__", or None for the initial exception.

    Notes
    -----
    Handles both explicit chaining (raised from) and implicit chaining (during handling).
    Adapted from the Python `pdb` module.
    """
    _exceptions = []
    current = exc
    reason = None

    while current is not None:
        if (current, reason) in _exceptions:
            break
        _exceptions.append((current, reason))

        if current.__cause__ is not None:
            current = current.__cause__
            reason = "__cause__"
        elif current.__context__ is not None and not current.__suppress_context__:
            current = current.__context__
            reason = "__context__"

    return reversed(_exceptions)


def retrieve_the_last_exception() -> Exception:
    """
    Get the last exception that was raised in the current thread.

    Returns
    -------
    Exception
        The last exception object, or None if no exception was raised.
    """
    # Python >= 3.12 | check python version
    if sys.version_info >= (3, 12):
        if hasattr(sys, "last_exec"):
            return sys.last_exec
        return None
    # Python <= 3.11
    if hasattr(sys, "last_value"):
        return sys.last_value
    return None


def extract_from_exception(
    exception: Exception, context_lines: int = 5, max_indent: int = 8
) -> Tuple[str, List[Dict]]:
    """
    Extract and format all chained exceptions with complete traceback information.

    Processes the full exception chain (including cause and context exceptions)
    and creates a comprehensive traceback report showing how exceptions are related.

    Parameters
    ----------
    exception : Exception
        The exception to process. Uses sys.last_value if None.
    context_lines : int, default 5
        Number of source code lines to include around each error line.
    max_indent : int, default 8
        Maximum code indentation to preserve in the output.

    Returns
    -------
    traceback_message : str
        Formatted human-readable traceback message with frame information and code context.
    frame_info : List[Dict]
        List of dictionaries containing detailed information about each frame:
        - message: str, formatted frame message
        - frame: frame object
        - locals: dict, local variables at the frame
        - globals: dict, global variables at the frame
        - metadata: dict with frame details (filename, line number, function name, etc.)

    Notes
    -----
    Unlike process_single_exception, this function handles the entire exception
    chain, including both __cause__ (explicit "raise from") and __context__
    (implicit "during handling of") relationships between exceptions.
    """
    if exception is None:
        exception = retrieve_the_last_exception()
        if exception is None:
            raise ValueError("No exception provided and no last exception found.")

    frames_info = []
    traceback_message = []

    for exc_value, exc_reason in get_chained_exceptions(exception):
        traceback_message_single, frame_info_single = process_single_exception(
            exc_value, context_lines, max_indent, frame_index=len(frames_info)
        )
        traceback_message.append(traceback_message_single)
        frames_info.extend(frame_info_single)

        if exc_reason == "__context__":
            traceback_message.append(
                "\n\nDuring handling of the above exception, another exception occurred:\n\n"
            )
        elif exc_reason == "__cause__":
            traceback_message.append(
                "\n\nThe above exception was the direct cause of the following exception:\n\n"
            )

    traceback_message = "\n".join(traceback_message)
    return traceback_message, frames_info


def execute(source: str, context: Dict) -> None:
    """
    Execute Python source code within a specified execution context.

    Parameters
    ----------
    source : str
        Python source code to execute. Will be automatically dedented
        to handle indentation from multi-line strings.
    context : Dict
        Dictionary containing execution context with keys:
        - 'globals': dict of global variables
        - 'locals': dict of local variables

    Returns
    -------
    None
        The function executes the code for its side effects only.

    Notes
    -----
    The source code is compiled before execution for better performance.
    """
    source = textwrap.dedent(source)
    # compile for better performance
    code = compile(source, "<string>", "exec")
    exec(code, context["globals"], context["locals"])  # noqa: S102
