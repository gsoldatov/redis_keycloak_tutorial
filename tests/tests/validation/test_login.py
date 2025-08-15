"""
/login route validation tests.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 4)))
    from tests.util import run_pytest_tests

from httpx import AsyncClient

from tests.data_generators import DataGenerator


async def test_validation(
    cli_no_cache_and_kc: AsyncClient,
    data_generator: DataGenerator
):
    # Invalid request body
    resp = await cli_no_cache_and_kc.post("/login", content=b"Not a JSON")
    assert resp.status_code == 422

    # Missing top-level params
    for attr in ("username", "password"):
        body = data_generator.auth.get_login_credentials_request_body()
        body.pop(attr)
        resp = await cli_no_cache_and_kc.post("/login", json=body)
        assert resp.status_code == 422
    
    # Unallowed attributes
    body = data_generator.auth.get_login_credentials_request_body()
    body["unallowed"] = "some value"
    resp = await cli_no_cache_and_kc.post("/login", json=body)
    assert resp.status_code == 422

    # Incorrect param values
    incorrect_values = {
        "username": [1, False, [], {}, ""],
        "password": [1, False, [], {}, ""]
    }
    for attr in incorrect_values:
        for value in incorrect_values[attr]:
            body = data_generator.auth.get_login_credentials_request_body()
            body[attr] = value
            resp = await cli_no_cache_and_kc.post("/login", json=body)
            assert resp.status_code == 422



if __name__ == "__main__":
    run_pytest_tests(__file__) # type: ignore[reportPossiblyUnboundVariable]
