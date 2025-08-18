from pathlib import Path

import typer

if __name__ == "__main__":
    import sys
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

from config import load_config
from src.keycloak.container import get_keycloak_container_manager
from src.keycloak.setup import reset_keycloak_app_realm, reset_keycloak_app_realm_users


config = load_config()
app = typer.Typer(pretty_exceptions_enable=False)
""" CLI utility for managing development containers. """


@app.command(help="Starts and configures containers.")
def run(
    debug: bool = False
):
    kc_container_manager = get_keycloak_container_manager(config.keycloak, debug)
    existed_before_run = kc_container_manager.exists()

    # Run or start Keycloak container
    kc_container_manager.run()

    # Run initial Keycloak configuration, if container is run for the first time
    if not existed_before_run:
        reset_keycloak_app_realm(config.keycloak)
        reset_keycloak_app_realm_users(config.keycloak)


@app.command(help="Stops running containers.")
def stop(
    debug: bool = False
):
    kc_container_manager = get_keycloak_container_manager(config.keycloak, debug)
    kc_container_manager.stop()


@app.command(help="Stops and removes containers and their volumes.")
def remove(
    debug: bool = False
):
    kc_container_manager = get_keycloak_container_manager(config.keycloak, debug)
    kc_container_manager.remove()


if __name__ == "__main__":
    app()
