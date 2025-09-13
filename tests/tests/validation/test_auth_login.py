"""
/auth/login route validation tests.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 4)))
    from tests.util import run_pytest_tests

from pydantic import ValidationError
import pytest

from src.app.models import UserCredentials
from tests.data_generators import DataGenerator


def test_incorrect_values(data_generator: DataGenerator):
    # Missing top-level params
    for attr in ("username", "password"):
        data = data_generator.auth.get_auth_login_request_body()
        data.pop(attr)
        with pytest.raises(ValidationError):
            UserCredentials(**data)
    
    # Unallowed attributes
    data = data_generator.auth.get_auth_login_request_body()
    data["unallowed"] = "some value"
    with pytest.raises(ValidationError):
        UserCredentials(**data)

    # Incorrect param values
    incorrect_values = {
        "username": [1, False, [], {}, "a" * 7, "a" * 33],
        "password": [1, False, [], {}, "a" * 7, "a" * 33]
    }
    for attr in incorrect_values:
        for value in incorrect_values[attr]:
            data = data_generator.auth.get_auth_login_request_body()
            data[attr] = value
            with pytest.raises(ValidationError):
                UserCredentials(**data)


def test_correct_values(data_generator: DataGenerator):
    values = {
        "username": ["a" * 8, "a" * 32],
        "password": ["a" * 8, "a" * 32]
    }
    for attr in values:
        for value in values[attr]:
            data = data_generator.auth.get_auth_login_request_body()
            data[attr] = value
            UserCredentials(**data)


if __name__ == "__main__":
    run_pytest_tests(__file__) # type: ignore[reportPossiblyUnboundVariable]
