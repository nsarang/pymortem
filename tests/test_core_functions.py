from pymortem import core


class TestProcessSingleException:
    def test_basic_exception_processing(self, generate_exception):
        """Test basic exception processing functionality"""
        e = generate_exception
        traceback_msg, frame_info = core.process_single_exception(e)

        # Verify traceback message contains proper elements
        assert "ZeroDivisionError: division by zero" in traceback_msg
        assert "Frame 0" in traceback_msg

        # Verify frame info structure
        assert isinstance(frame_info, list)
        assert len(frame_info) > 0
        assert "message" in frame_info[0]
        assert "frame" in frame_info[0]
        assert "locals" in frame_info[0]
        assert "globals" in frame_info[0]
        assert "metadata" in frame_info[0]

    def test_context_lines_parameter(self):
        """Test that context_lines parameter works correctly"""

        def error_function():
            # Line before
            x = 5
            # Error line
            result = x / 0
            # Line after
            return result

        try:
            error_function()
        except Exception as e:
            # Test with 1 context line (minimum allowed)
            msg1, info1 = core.process_single_exception(e, context_lines=1)
            # Test with 3 context lines
            msg3, info3 = core.process_single_exception(e, context_lines=3)

            # Find the frame containing "x / 0" in each case
            def find_error_frame(frames):
                for frame in frames:
                    if any("x / 0" in line for line in frame["metadata"]["lines"]):
                        return frame
                return None

            error_frame1 = find_error_frame(info1)
            error_frame3 = find_error_frame(info3)

            # Check that we found the frames
            assert error_frame1 is not None, "Error frame not found with context_lines=1"
            assert error_frame3 is not None, "Error frame not found with context_lines=3"

            # Verify different context sizes
            assert len(error_frame1["metadata"]["lines"]) < len(error_frame3["metadata"]["lines"])

            # The error line should be present in both cases
            assert any("x / 0" in line for line in error_frame1["metadata"]["lines"])
            assert any("x / 0" in line for line in error_frame3["metadata"]["lines"])

    def test_max_indent_parameter(self):
        """Test that max_indent parameter correctly reformats indentation"""

        def deeply_nested_function():
            def inner_function():
                if True:
                    if True:
                        if True:
                            # This is deeply indented
                            x = 10
                            return x / 0

            return inner_function()

        try:
            deeply_nested_function()
        except Exception as e:
            # Process with unlimited indentation
            msg1, info_default = core.process_single_exception(e)
            # Process with limited indentation (4 spaces max)
            msg2, info_limited = core.process_single_exception(e, max_indent=4)

            # Find the frame containing the error line in each case
            def find_error_frame_and_line(frames, text="x / 0"):
                for frame in frames:
                    for line in frame["metadata"]["lines"]:
                        if text in line:
                            return frame, line
                return None, None

            _, default_line = find_error_frame_and_line(info_default)
            _, limited_line = find_error_frame_and_line(info_limited)

            # Verify we found the lines
            assert default_line is not None, "Error line not found with default indentation"
            assert limited_line is not None, "Error line not found with limited indentation"

            # Count leading spaces
            default_indent = len(default_line) - len(default_line.lstrip())
            limited_indent = len(limited_line) - len(limited_line.lstrip())

            # Check that indentation limitation works
            assert limited_indent <= 4, f"Expected max indent of 4, got {limited_indent}"
            # Only assert the unlimited indent is larger if it actually is (depends on the original code)
            if default_indent > 4:
                assert default_indent > limited_indent, "Limiting indentation had no effect"


class TestExecute:
    def test_execute_simple_code(self):
        """Test executing simple code in a context"""
        # Create a simple context
        context = {"globals": {"global_var": 5}, "locals": {"local_var": 10}}

        # Execute code that modifies the context
        core.execute(
            """
        result = local_var + global_var
        new_var = result * 2
        """,
            context,
        )

        # Check the modifications took effect
        assert context["locals"]["result"] == 15
        assert context["locals"]["new_var"] == 30

    def test_execute_with_indentation(self):
        """Test that indented code is properly dedented"""
        context = {"globals": {}, "locals": {"value": 5}}

        # Execute indented code
        core.execute(
            """
            # This is indented code
            if value > 0:
                result = "positive"
            else:
                result = "non-positive"
        """,
            context,
        )

        # Verify execution was successful
        assert context["locals"]["result"] == "positive"

    def test_execute_with_exception_frame(self, generate_exception):
        """Test executing code in an actual exception frame context"""
        _, frames = core.extract_from_exception(generate_exception)

        # Execute code in the frame context
        core.execute(
            """
        # Create new variables
        debug_info = "Processing exception"
        error_type = "Division by zero"
        """,
            frames[0],
        )

        # Verify the execution worked properly
        assert frames[0]["locals"]["debug_info"] == "Processing exception"
        assert frames[0]["locals"]["error_type"] == "Division by zero"
