from util.container_manager import ContainerManager

from config import KeycloakConfig


def get_keycloak_container_manager(
        kc_config: KeycloakConfig,
        debug: bool
    ):
    return ContainerManager(
        name="keycloak_redis_tutorial_keycloak",
        run_args=[
            # Expose Keycloak on custom ports
            "-p", f"{kc_config.container_main_port}:8080",
            "-p", f"{kc_config.container_healthcheck_port}:9000",

            # Admin credentials
            "-e", f"KC_BOOTSTRAP_ADMIN_USERNAME={kc_config.admin_username}",
            "-e", f"KC_BOOTSTRAP_ADMIN_PASSWORD={kc_config.admin_password}",

            # Enable healthcheck service
            "-e", "KC_HEALTH_ENABLED=true",

            # # Provide custom healthcheck params for Docker
            # # https://gist.github.com/sarath-soman/5d9aec06953bbd0990c648605d4dba07?permalink_comment_id=5225953#gistcomment-5225953
            # """--health-cmd="exec 3<>/dev/tcp/127.0.0.1/9000; echo -e 'GET /health/ready HTTP/1.1\r\nHost: localhost:9000\r\nConnection: close\r\n\r\n' >&3;cat <&3 | grep -q '\"status\": \"UP\"' && exit 0 || exit 1" """,
            # "--health-interval=5s",
            # "--health-retries=3",
            # "--health-timeout=10s",
        ],

        image="quay.io/keycloak/keycloak:latest",

        run_command_args=[
            # Run in development mode
            "start-dev",
            
            # Enable custom port usage on Keycloak side
            f"--hostname", kc_config.keycloak_url,
        ],
        debug=debug
    )
