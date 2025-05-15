from pymortem import core


class TestIntegrationScenarios:
    def test_nested_function_exceptions(self):
        """Test with exceptions in nested function calls"""

        def level3():
            data = [1, 2, 3]
            return data[5]  # IndexError

        def level2():
            return level3()

        def level1():
            return level2()

        try:
            level1()
        except Exception as e:
            msg, frames = core.extract_from_exception(e)

            # Verify we captured all levels of the call stack
            function_names = [f["metadata"]["function_name"] for f in frames]
            assert "level1" in function_names
            assert "level2" in function_names
            assert "level3" in function_names

            # Verify the error information is correct
            assert "IndexError" in msg
            assert any("data[5]" in f["message"] for f in frames)

            # Find the frame with the actual error
            error_frame = None
            for frame in frames:
                if frame["metadata"]["function_name"] == "level3":
                    error_frame = frame
                    break

            assert error_frame is not None
            # The data list should be in the locals
            assert "data" in error_frame["locals"]
            assert error_frame["locals"]["data"] == [1, 2, 3]

    def test_different_exception_types(self):
        """Test with various types of exceptions"""
        exceptions_to_test = [
            (lambda: 1 / 0, ZeroDivisionError),  # Arithmetic
            (lambda: int("not a number"), ValueError),  # Value
            (lambda: [1, 2, 3][10], IndexError),  # Index # noqa: PLE0643
            (lambda: {"a": 1}["b"], KeyError),  # Key
            (lambda: open("nonexistent_file"), FileNotFoundError),  # IO
        ]

        for func, expected_type in exceptions_to_test:
            try:
                func()
            except Exception as e:
                assert isinstance(e, expected_type)
                msg, frames = core.extract_from_exception(e)

                # Verify exception type is in the message
                assert expected_type.__name__ in msg

                # Verify frame info is correct
                assert len(frames) > 0
                assert "frame" in frames[0]
                assert "locals" in frames[0]
                assert "globals" in frames[0]

    def test_recursive_function_with_exception(self):
        """Test exception in a recursive function call"""

        def recursive_function(n):
            # Local variables to track
            call_depth = n  # noqa: F841
            if n <= 0:
                # Trigger exception at recursion end
                x = None
                return x.attribute  # AttributeError
            return recursive_function(n - 1)

        try:
            recursive_function(3)
        except Exception as e:
            msg, frames = core.extract_from_exception(e)

            # Check that we have multiple recursive frames
            recursive_frames = [
                f for f in frames if f["metadata"]["function_name"] == "recursive_function"
            ]

            # Should have 4 recursive frames (initial + 3 recursions)
            assert len(recursive_frames) >= 4

            # Verify the different call_depth values in each frame
            depths = sorted([frame["locals"].get("call_depth") for frame in recursive_frames])
            assert depths == [0, 1, 2, 3]

            # Execute code in the frame where the error occurred (depth 0)
            error_frame = next(f for f in recursive_frames if f["locals"]["call_depth"] == 0)

            # Try fixing the error within the context
            core.execute(
                """
            x = 'fixed'  # Replace None with a string
            fixed_result = x + " result"  # This would work now
            """,
                error_frame,
            )

            # Verify our fix worked in the context
            assert error_frame["locals"]["x"] == "fixed"
            assert error_frame["locals"]["fixed_result"] == "fixed result"
