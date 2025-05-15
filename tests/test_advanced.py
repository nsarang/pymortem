import pytest

from pymortem import core


class TestAdvancedScenarios:
    def test_exception_in_generator(self):
        """Test capturing exceptions in generator functions"""

        def generator_function():
            yield 1
            yield 2
            # This will raise an exception when next() is called the third time
            yield 1 / 0

        gen = generator_function()
        next(gen)  # 1
        next(gen)  # 2

        try:
            next(gen)  # Will raise ZeroDivisionError
        except Exception as e:
            msg, frames = core.extract_from_exception(e)

            # Verify the exception is from the generator
            assert "ZeroDivisionError" in msg
            # Find the generator frame
            gen_frame = next(
                (f for f in frames if f["metadata"]["function_name"] == "generator_function"), None
            )
            assert gen_frame is not None

    @pytest.mark.asyncio
    async def test_exception_in_async_function(self):
        """Test exceptions in async functions (requires Python 3.6+)"""
        import asyncio

        async def async_function():
            await asyncio.sleep(0.001)
            result = 1 / 0
            return result

        with pytest.raises(ZeroDivisionError) as excinfo:
            await async_function()

        msg, frames = core.extract_from_exception(excinfo.value)

        # Verify the exception captures the async context
        assert "ZeroDivisionError" in msg
        async_frame = next(
            (f for f in frames if f["metadata"]["function_name"] == "async_function"), None
        )
        assert async_frame is not None

    def test_custom_exception_class(self):
        """Test with custom exception classes"""

        class CustomError(Exception):
            def __init__(self, value, extra_info=None):
                self.value = value
                self.extra_info = extra_info
                super().__init__(f"Custom error: {value}")

        try:
            raise CustomError("test value", extra_info="additional data")
        except Exception as e:
            msg, frames = core.extract_from_exception(e)

            # Verify custom exception details are captured
            assert "CustomError" in msg
            assert "test value" in msg

            # Access exception attributes through the frame
            frame = frames[0]
            # The exception object itself isn't directly in the frame locals,
            # but we can execute code to extract attributes
            core.execute(
                """
            # Get the exception that was thrown
            import sys
            e = sys.exc_info()[1]
            # Extract custom attributes
            extracted_value = e.value
            extracted_extra = e.extra_info
            """,
                frame,
            )

            # Verify we extracted the custom attributes
            assert frame["locals"]["extracted_value"] == "test value"
            assert frame["locals"]["extracted_extra"] == "additional data"
