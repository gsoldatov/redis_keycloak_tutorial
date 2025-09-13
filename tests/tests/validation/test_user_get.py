"""
GET /users/:username route validation tests.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 4)))
    from tests.util import run_pytest_tests

from pydantic import BaseModel, ValidationError
import pytest

from src.app.models import Username


class TestModel(BaseModel):
    username: Username


def test_incorrect_values():
    for value in [None, False, 1, [], {}, "a" * 7, "a" * 33]:
        with pytest.raises(ValidationError):
            TestModel(username=value)


def test_correct_values():
    for value in ["a" * 8, "a" * 32]:
        TestModel(username=value)


if __name__ == "__main__":
    run_pytest_tests(__file__) # type: ignore[reportPossiblyUnboundVariable]
