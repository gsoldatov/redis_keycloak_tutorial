"""
/auth/register route validation tests.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 4)))
    from tests.util import run_pytest_tests

from pydantic import ValidationError
import pytest

from src.app.models import UserRegistrationCredentials
from tests.data_generators import DataGenerator


def test_incorrect_values(data_generator: DataGenerator):
    # Missing top-level params
    for attr in ("email", "username", "first_name", "last_name", "password", "password_repeat"):
        data = data_generator.auth.get_auth_register_request_body()
        data.pop(attr)
        with pytest.raises(ValidationError):
            UserRegistrationCredentials(**data)
    
    # Unallowed attributes
    data = data_generator.auth.get_auth_register_request_body()
    data["unallowed"] = "some value"
    with pytest.raises(ValidationError):
        UserRegistrationCredentials(**data)

    # Incorrect param values
    incorrect_values = {
        # NOTE: see comment in valid values test for email max lengths
        "email": [1, False, [], {}, "not an email", "a" * 65 + "@example.com", "addr@" + "a" * (255 - 5 - 4) + ".com"],
        "username": [1, False, [], {}, "a" * 7, "a" * 33],
        "first_name": [1, False, [], {}, "", "a" * 65],
        "last_name": [1, False, [], {}, "", "a" * 65],
        "password": [1, False, [], {}, "a" * 7, "a" * 33]
    }
    for attr in incorrect_values:
        for value in incorrect_values[attr]:
            data = data_generator.auth.get_auth_register_request_body()
            data[attr] = value
            with pytest.raises(ValidationError):
                UserRegistrationCredentials(**data)
    
    # Password repeat does not match
    data = data_generator.auth.get_auth_register_request_body(password="password")
    data["password_repeat"] = "not matching password repeat"
    with pytest.raises(ValidationError):
        UserRegistrationCredentials(**data)


def test_correct_values(data_generator: DataGenerator):
    values = {
        "email": [
            "email@example.com",
            "a" * 64 + "@example.com",
            # email max lengths, according to email_validator lib:
            # - total - 254 chars;
            # - local part (before @) - 63 chars;
            # - dns parts - 63 chars each
            "addr@" + ("a" * 63 + ".") * 3 + "a" * (254 - 5 - 64 * 3 - 4) + ".com"
        ],
        "username": ["a" * 8, "a" * 32],
        "first_name": ["a" * 8, "a" * 64],
        "last_name": ["a" * 8, "a" * 64],
        "password": ["a" * 8, "a" * 32]
    }
    for attr in values:
        for value in values[attr]:
            data = data_generator.auth.get_auth_register_request_body()
            data[attr] = value
            if attr == "password":
                data["password_repeat"] = value
            UserRegistrationCredentials(**data)


if __name__ == "__main__":
    run_pytest_tests(__file__) # type: ignore[reportPossiblyUnboundVariable]
