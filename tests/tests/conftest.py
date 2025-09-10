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
from src.redis.container import get_redis_container_manager

from tests.data_generators import DataGenerator


############ Session-scoped fixtures ############
@pytest.fixture(scope="session")
def config() -> Config:
    return load_config()


@pytest.fixture(scope="session")
def keycloak_container(config: Config):
    manager = get_keycloak_container_manager(config.keycloak, True)
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
def redis_container(config: Config):
    manager = get_redis_container_manager(config.redis, True)
    if not manager.is_running():
        manager.run()
    yield


############ Module-scoped fixtures (configs) ############
@pytest.fixture(scope="module")
def test_config(config: Config) -> Config:
    postfix = uuid4().hex
    test_config = Config.model_validate(config.model_dump())
    test_config.keycloak.app_realm_name = f"test_{postfix}"
    return test_config


@pytest.fixture(scope="module")
def config_with_unavailable_keycloak_and_redis(config: Config) -> Config:
    """ Test config with its Keycloak and Redis container ports changed to incorrect values. """
    updated_config = Config.model_validate(config.model_dump())
    updated_config.keycloak.container_main_port += 1000
    updated_config.keycloak.container_healthcheck_port += 1000
    updated_config.redis.container_port += 1000
    return updated_config


############ Module-scoped fixtures (Keycloak) ############
@pytest.fixture(scope="module")
def keycloak_manager(test_config: Config, keycloak_container: None):
    """ Wait for Keycloak to be ready & yield a KeycloakManager instance. """
    with KeycloakManager(test_config.keycloak) as manager:
        yield manager


@pytest.fixture(scope="module")
def test_keycloak_realm(
    test_config: Config,
    keycloak_manager: KeycloakManager
):
    """ Setup & teardown test Keycloak realm and return default configuration. """
    keycloak_manager.delete_app_realm()

    keycloak_manager.create_app_realm()
    keycloak_manager.create_app_client()
    keycloak_manager.add_client_role("role-1")
    keycloak_manager.add_client_role("role-2")

    client_representtation = keycloak_manager.get_app_client()

    yield (client_representtation, )
    
    keycloak_manager.delete_app_realm()


############ Module-scoped fixtures (Redis) ############


############ Test-scoped fixtures (common) ############
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
def restore_keycloak_configuration(
    test_keycloak_realm: tuple,
    keycloak_manager: KeycloakManager
    
):
    """ Restores realm configuration after each test. """
    yield

    # Delete existing users in the test realm
    keycloak_manager.delete_all_users()

    # Restore client state
    keycloak_manager.update_app_client(test_keycloak_realm[0])


@pytest.fixture
def app_no_kc_and_redis(anyio_backend, config_with_unavailable_keycloak_and_redis):
    return create_app(config_with_unavailable_keycloak_and_redis) 


@pytest.fixture
async def cli_no_kc_and_redis(app_no_kc_and_redis):
    """
    Yields a test client for the application.
    Keycloak and Redis ports are set to incorrect values
    to simulate their unavailability.
    """
    # Enable app's lifespan events in test environment
    # https://fastapi.tiangolo.com/advanced/async-tests
    async with LifespanManager(app_no_kc_and_redis) as manager:
        async with AsyncClient(
            transport=ASGITransport(app=manager.app), base_url="http://test"
        ) as async_client:
            yield async_client

@pytest.fixture
def app_no_redis(anyio_backend, test_config):
    return create_app(test_config)


@pytest.fixture
async def cli_no_redis(
        app_no_redis,
        restore_keycloak_configuration
    ):
    """ Yields a test client for the application without cache enabled. """
    # Enable app's lifespan events in test environment
    # https://fastapi.tiangolo.com/advanced/async-tests
    async with LifespanManager(app_no_redis) as manager:
        async with AsyncClient(
            transport=ASGITransport(app=manager.app), base_url="http://test"
        ) as async_client:
            yield async_client
