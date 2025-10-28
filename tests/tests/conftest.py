import os
import sys
from pathlib import Path
from uuid import uuid4

from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
import filelock
import pytest

project_root_dir = os.path.abspath(os.path.join(__file__, "../" * 3))
sys.path.insert(0, project_root_dir)

from config import load_config, Config

from src.app.main import create_app

from src.keycloak.container import get_keycloak_container_manager
from src.keycloak.admin import KeycloakAdminClient, ALL_ROLES
from src.redis.container import get_redis_container_manager
from src.redis.admin import RedisAdminClient

from tests.data_generators import DataGenerator
from tests.shared_test_state import SharedTestStateManager


# File locks for container fixtures
_lock_dir = Path(__file__).parent
_redis_container_lock_path = _lock_dir / "redis_container.lock"
_keycloak_container_lock_path = _lock_dir / "keycloak_container.lock"
redis_container_lock = filelock.FileLock(_redis_container_lock_path, timeout=120)
keycloak_container_lock = filelock.FileLock(_keycloak_container_lock_path, timeout=120)


############ Session-scoped fixtures ############
@pytest.fixture(scope="session")
def reset_shared_test_state(testrun_uid) -> None:
    """ Reset shared state file. """
    SharedTestStateManager().reset_state(testrun_uid)


@pytest.fixture(scope="session")
def config(
    reset_shared_test_state     # Trigger shared state file reset for all tests
) -> Config:
    return load_config()


@pytest.fixture(scope="session")
def keycloak_container(config: Config):
    manager = get_keycloak_container_manager(config.keycloak, True)

    # Use a lock to avoid multiple attempts to run a container,
    # if it's not up
    with keycloak_container_lock:
        if not manager.is_running():
            manager.run()
    
    yield
    
    # NOTE: with xdist enabled, fixture is not guaranteed to execute exactly once;
    # this results is container being stopped prematurely;
    # a workaround would be to memoize `manager.is_running()` value on first call
    # (via a file lock, for example), and to retrieve it in the last worker,
    # which would stop the container, if needed


@pytest.fixture(scope="session")
def redis_container(config: Config):
    manager = get_redis_container_manager(config.redis, True)

    # Use a lock to avoid multiple attempts to run a container,
    # if it's not up
    with redis_container_lock:
        if not manager.is_running():
            manager.run()
    
    yield


############ Module-scoped fixtures (configs) ############
@pytest.fixture(scope="module")
def test_config(config: Config) -> Config:
    postfix = uuid4().hex
    test_config = Config.model_validate(config.model_dump())

    # Test Keycloak settings
    test_config.keycloak.app_realm_name = f"test_{postfix}"

    # Test Redis settings
    test_config.redis.database = SharedTestStateManager().get_free_redis_database_number()
    test_config.redis.socket_timeout = 0.25
    test_config.redis.number_of_retries = 0

    return test_config


@pytest.fixture(scope="module")
def config_with_unavailable_keycloak_and_redis(test_config: Config) -> Config:
    """ Test config with its Keycloak and Redis container ports changed to incorrect values. """
    updated_config = Config.model_validate(test_config.model_dump())
    updated_config.keycloak.container_main_port += 1000
    updated_config.keycloak.container_healthcheck_port += 1000
    updated_config.redis.container_port += 1000
    return updated_config


@pytest.fixture(scope="module")
def config_with_unavailable_keycloak(test_config: Config) -> Config:
    """ Test config with its Keycloak container ports changed to incorrect values. """
    updated_config = Config.model_validate(test_config.model_dump())
    updated_config.keycloak.container_main_port += 1000
    updated_config.keycloak.container_healthcheck_port += 1000
    return updated_config


@pytest.fixture(scope="module")
def config_with_unavailable_redis(test_config: Config) -> Config:
    """ Test config with its Redis container ports changed to incorrect values. """
    updated_config = Config.model_validate(test_config.model_dump())
    updated_config.redis.container_port += 1000
    return updated_config


############ Module-scoped fixtures (Keycloak) ############
@pytest.fixture(scope="module")
def keycloak_admin_client(test_config: Config, keycloak_container: None):
    """ Wait for Keycloak to be ready & yield a KeycloakAdminClient instance. """
    with KeycloakAdminClient(test_config.keycloak) as client:
        yield client


@pytest.fixture(scope="module")
def test_keycloak_realm(
    test_config: Config,
    keycloak_admin_client: KeycloakAdminClient
):
    """ Setup & teardown test Keycloak realm and return default configuration. """
    keycloak_admin_client.delete_app_realm()

    keycloak_admin_client.create_app_realm()
    keycloak_admin_client.create_app_client()
    for role in ALL_ROLES:
        keycloak_admin_client.add_client_role(role)

    client_representtation = keycloak_admin_client.get_app_client()

    yield (client_representtation, )
    
    keycloak_admin_client.delete_app_realm()


############ Module-scoped fixtures (Redis) ############
@pytest.fixture(scope="module")
def redis_admin_client(test_config: Config, redis_container: None):
    """ Wait for Redis to be ready & yield an admin client. """
    with RedisAdminClient(test_config.redis) as client:
        yield client


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
    keycloak_admin_client: KeycloakAdminClient
    
):
    """ Restores realm configuration after each test. """
    yield

    # Delete existing users in the test realm
    keycloak_admin_client.delete_all_users()

    # Restore client state
    keycloak_admin_client.update_app_client(test_keycloak_realm[0])


@pytest.fixture
def reset_redis_database(redis_admin_client: RedisAdminClient):
    """ Clears current Redis database after a test. """
    yield
    redis_admin_client.flush_db()


############ Test-scoped fixtures (no Keycloak & Redis) ############
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


############ Test-scoped fixtures (no Redis) ############
@pytest.fixture
def app_no_keycloak(anyio_backend, config_with_unavailable_keycloak):
    return create_app(config_with_unavailable_keycloak)


@pytest.fixture
async def cli_no_keycloak(
        app_no_keycloak,
        reset_redis_database
    ):
    """ Yields a test client for the application without cache enabled. """
    # Enable app's lifespan events in test environment
    # https://fastapi.tiangolo.com/advanced/async-tests
    async with LifespanManager(app_no_keycloak) as manager:
        async with AsyncClient(
            transport=ASGITransport(app=manager.app), base_url="http://test"
        ) as async_client:
            yield async_client


############ Test-scoped fixtures (no Redis) ############
@pytest.fixture
def app_no_redis(anyio_backend, config_with_unavailable_redis):
    return create_app(config_with_unavailable_redis)


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


############ Test-scoped fixtures (with Keycloak & Redis) ############
@pytest.fixture
def app(anyio_backend, test_config):
    return create_app(test_config)


@pytest.fixture
async def cli(
        app,
        restore_keycloak_configuration,
        reset_redis_database
    ):
    """ Yields a test client for the application without cache enabled. """
    # Enable app's lifespan events in test environment
    # https://fastapi.tiangolo.com/advanced/async-tests
    async with LifespanManager(app) as manager:
        async with AsyncClient(
            transport=ASGITransport(app=manager.app), base_url="http://test"
        ) as async_client:
            yield async_client
