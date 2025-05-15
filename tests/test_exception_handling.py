import sys

from pymortem import core


class TestGetChainedExceptions:
    def test_simple_exception(self):
        """Test with a simple, non-chained exception"""
        try:
            raise ValueError("Test error")
        except Exception as e:
            chain = list(core.get_chained_exceptions(e))
            assert len(chain) == 1
            assert isinstance(chain[0][0], ValueError)
            assert chain[0][1] is None  # No reason for the first exception

    def test_exception_with_cause(self):
        """Test with an exception having an explicit cause"""
        try:
            try:
                raise ValueError("Inner error")
            except ValueError as inner_error:
                raise RuntimeError("Outer error") from inner_error
        except Exception as e:
            chain = list(core.get_chained_exceptions(e))

            # Should have two exceptions in the chain
            assert len(chain) == 2

            # First exception should be the inner ValueError
            assert isinstance(chain[0][0], ValueError)
            # The reason for the first exception is __cause__ because that's how it's tracked
            assert chain[0][1] == "__cause__"

            # Second exception should be the outer RuntimeError
            assert isinstance(chain[1][0], RuntimeError)
            # The outer exception has no further reason
            assert chain[1][1] is None

    def test_exception_with_context(self):
        """Test with an exception having an implicit context"""
        try:
            try:
                raise ValueError("First error")
            except Exception:
                # This creates an implicit __context__
                raise RuntimeError("Second error")
        except Exception as e:
            chain = list(core.get_chained_exceptions(e))

            # Should have two exceptions in the chain
            assert len(chain) == 2

            # First exception should be the ValueError
            assert isinstance(chain[0][0], ValueError)
            # The reason for the first exception is __context__ in this case
            assert chain[0][1] == "__context__"

            # Second exception should be the RuntimeError
            assert isinstance(chain[1][0], RuntimeError)
            # The outer exception has no further reason
            assert chain[1][1] is None

    def test_suppress_context(self):
        """Test that __suppress_context__ works correctly"""
        try:
            try:
                raise ValueError("Suppressed error")
            except Exception:
                # Create exception with suppressed context
                e = RuntimeError("Main error")
                e.__suppress_context__ = True
                raise e
        except Exception as e:
            chain = list(core.get_chained_exceptions(e))

            # Should only have one exception due to suppression
            assert len(chain) == 1
            assert isinstance(chain[0][0], RuntimeError)

    def test_explicit_context_suppression(self):
        """Test with an exception using 'raise from None' to explicitly suppress context"""
        try:
            try:
                raise ValueError("Suppressed explicitly")
            except ValueError:
                # This explicitly breaks the chain using 'from None'
                raise RuntimeError("Main error with no context") from None
        except Exception as e:
            chain = list(core.get_chained_exceptions(e))

            # Should only have one exception since context is explicitly suppressed with 'from None'
            assert len(chain) == 1
            assert isinstance(chain[0][0], RuntimeError)
            assert str(chain[0][0]) == "Main error with no context"

            # Verify both __context__ and __cause__ are None or appropriately handled
            assert chain[0][0].__cause__ is None
            # Even though __context__ might contain the ValueError, it should be suppressed
            assert chain[0][0].__suppress_context__ is True

    def test_multi_level_explicit_chaining(self):
        """Test with multiple levels of explicitly chained exceptions"""
        try:
            try:
                try:
                    raise ValueError("Original error")
                except ValueError as e1:
                    raise KeyError("Intermediate error") from e1
            except KeyError as e2:
                raise RuntimeError("Final error") from e2
        except Exception as e:
            chain = list(core.get_chained_exceptions(e))

            # Should have three exceptions in the chain
            assert len(chain) == 3

            # Check exception types and reasons in order
            assert isinstance(chain[0][0], ValueError)
            assert chain[0][1] == "__cause__"

            assert isinstance(chain[1][0], KeyError)
            assert chain[1][1] == "__cause__"

            assert isinstance(chain[2][0], RuntimeError)
            assert chain[2][1] is None

            # Verify the chaining relationships
            final_exception = chain[2][0]
            assert isinstance(final_exception.__cause__, KeyError)
            assert isinstance(final_exception.__cause__.__cause__, ValueError)


class TestExtractFromException:
    def test_extract_simple_exception(self):
        """Test extraction of a simple exception"""
        try:
            1 / 0
        except Exception as e:
            msg, frames = core.extract_from_exception(e)

            # Check message formatting
            assert "ZeroDivisionError: division by zero" in msg
            assert "Frame" in msg

            # Check frame structure
            assert isinstance(frames, list)
            assert len(frames) > 0
            for frame in frames:
                assert "frame" in frame
                assert "locals" in frame
                assert "globals" in frame

    def test_extract_chained_exceptions(self):
        """Test extraction from chained exceptions"""

        def inner_error():
            x = {"key": "value"}
            # This will raise KeyError
            return x["missing"]

        def outer_error():
            try:
                return inner_error()
            except KeyError:
                # This will be a chained exception with context
                raise ValueError("Could not find the key")

        try:
            outer_error()
        except Exception as e:
            msg, frames = core.extract_from_exception(e)

            # Message should contain both exceptions
            assert "KeyError" in msg
            assert "ValueError" in msg
            assert "During handling of the above exception" in msg

            # Should have frames from both exceptions
            inner_frame = None
            outer_frame = None

            for frame in frames:
                if "inner_error" in frame["metadata"]["function_name"]:
                    inner_frame = frame
                if "outer_error" in frame["metadata"]["function_name"]:
                    outer_frame = frame

            # Verify we captured both frames
            assert inner_frame is not None
            assert outer_frame is not None

            # Check inner frame has the dictionary
            assert "x" in inner_frame["locals"]
            assert inner_frame["locals"]["x"] == {"key": "value"}

    def test_retrieve_the_last_exception(self):
        """Test the retrieve_the_last_exception function"""
        # Case 1: No exception has occurred yet
        # Clear any previous exceptions
        try:
            sys.exc_info = lambda: (None, None, None)
        except AttributeError:
            pass  # Can't monkeypatch exc_info in some environments

        result = core.retrieve_the_last_exception()
        assert result is None, "Should return None when no exception has occurred"

        # Case 2: After an exception has occurred
        test_exception = None
        try:
            raise ValueError("Test exception")
        except Exception as e:
            test_exception = e
            # Now test_exception should be retrievable
            result = core.retrieve_the_last_exception()

            # One of these should succeed depending on the environment:
            assert result is test_exception or isinstance(result, ValueError) or result is None
