from contextlib import contextmanager

import pytest


@contextmanager
def capture_exception():
    """Helper to capture and return an exception"""
    try:
        yield
    except Exception as e:
        return e
    pytest.fail("Expected exception was not raised")


@pytest.fixture
def generate_exception():
    """Fixture to generate a simple exception"""
    try:
        1 / 0
    except Exception as e:
        return e
