import os
import sys
from uuid import uuid4

from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
import pytest

project_root_dir = os.path.abspath(os.path.join(__file__, "../" * 3))
sys.path.insert(0, project_root_dir)

from config import load_config, Config

from src.app.main import create_app

from src.keycloak.container import get_keycloak_container_manager
from src.keycloak.setup import KeycloakManager

from tests.data_generators import DataGenerator


############ Session fixtures ############
@pytest.fixture(scope="session")
def config() -> Config:
    return load_config()


@pytest.fixture(scope="session")
def config_with_unavailable_keycloak_and_cache(config: Config) -> Config:
    """ Test config with its Keycloak and Redis container ports changed to incorrect values. """
    updated_config = Config.model_validate(config.model_dump())
    updated_config.keycloak.container_main_port += 1000
    updated_config.keycloak.container_healthcheck_port += 1000
    return updated_config


@pytest.fixture(scope="session")
def keycloak_container(config):
    manager = get_keycloak_container_manager(config, True)
    if not manager.is_running():
        manager.run()
        yield
        
        # NOTE: with xdist enabled, fixture is not guaranteed to execute exactly once;
        # this results is container being stopped prematurely;
        # a workaround would be to memoize `manager.is_running()` value on first call
        # (via a file lock, for example), and to retrieve it in the last worker,
        # which would stop the container, if needed
        
        # manager.stop()
    else:
        yield


@pytest.fixture(scope="session")
def keycloak_ready(config: Config, keycloak_container):
    """ Ensure Keycloak container is ready. """
    manager = KeycloakManager(config.keycloak)
    manager.wait_for_server()


############ Module fixtures ############
@pytest.fixture(scope="module")
def test_config(config: Config) -> Config:
    postfix = uuid4().hex
    test_config = Config.model_validate(config.model_dump())
    test_config.keycloak.app_realm_name = f"test_{postfix}"
    return test_config


@pytest.fixture(scope="module")
def test_keycloak_realm_and_manager(test_config: Config):
    """ Setup test Keycloak realm (also check that container is ready). """
    with KeycloakManager(test_config.keycloak) as manager:
        manager.delete_app_realm()

        manager.create_app_realm()
        manager.create_app_client()
        manager.add_client_role("role-1")
        manager.add_client_role("role-2")

        yield manager
        
        manager.delete_app_realm()


############ Function fixtures ############
@pytest.fixture
def keycloak_manager(test_keycloak_realm_and_manager: KeycloakManager):
    """ Yields KeycloakManager for test realm & cleans up the realm after each test. """
    yield test_keycloak_realm_and_manager

    # Delete existing users in the test realm
    test_keycloak_realm_and_manager.delete_users()


@pytest.fixture
def data_generator():
    return DataGenerator()


@pytest.fixture
def anyio_backend():
    """
    Specify async engine to be used by AnyIO Pytest plugin;
    This also enables running async tests without marking them
    https://anyio.readthedocs.io/en/stable/testing.html
    """
    return "asyncio"


@pytest.fixture
async def cli_no_cache_and_kc(
        anyio_backend,
        config_with_unavailable_keycloak_and_cache
    ):
    """
    Yields a test client for the application.
    Keycloak and Redis ports are set to incorrect values
    to simulate their unavailability.
    """
    app = create_app(config_with_unavailable_keycloak_and_cache)
    # Enable app's lifespan events in test environment
    # https://fastapi.tiangolo.com/advanced/async-tests
    async with LifespanManager(app) as manager:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as async_client:
            yield async_client


@pytest.fixture
async def cli_no_cache(
        anyio_backend,
        test_config,
        keycloak_manager
    ):
    """ Yields a test client for the application without cache enabled. """
    app = create_app(test_config)
    # Enable app's lifespan events in test environment
    # https://fastapi.tiangolo.com/advanced/async-tests
    async with LifespanManager(app) as manager:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as async_client:
            yield async_client
