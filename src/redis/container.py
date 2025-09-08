from config import RedisConfig
from src.util.container_manager import ContainerManager



def get_redis_container_manager(
        redis_config: RedisConfig,
        debug: bool
    ):
    return ContainerManager(
        name=redis_config.container_name,
        run_args=[
            # Expose Redis on a custom port
            "-p", f"{redis_config.container_port}:6379"
        ],

        image="redis:8.2.1",

        run_command_args=[
            "redis-server",
            
            # Add a password for default user
            f'--requirepass "{redis_config.password}"'
        ],
        debug=debug
    )


def run_redis_container(
    redis_config: RedisConfig,
    debug: bool
):
    redis_container_manager = get_redis_container_manager(redis_config, debug)

    # Run or start Keycloak container
    redis_container_manager.run()
