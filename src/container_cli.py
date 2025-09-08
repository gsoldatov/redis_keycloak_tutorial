from pathlib import Path
import threading
import typer

if __name__ == "__main__":
    import sys
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

from config import load_config
from src.keycloak.container import get_keycloak_container_manager, run_keycloak_container
from src.redis.container import get_redis_container_manager, run_redis_container


config = load_config()
app = typer.Typer(pretty_exceptions_enable=False)
""" CLI utility for managing development containers. """


@app.command(help="Starts and configures containers.")
def run(
    debug: bool = False
):
    exceptions = []
    
    def run_with_exception(func, *args):
        try:
            func(*args)
        except Exception as e:
            exceptions.append(e)
    
    threads = [
        threading.Thread(
            target=run_with_exception,
            args=(run_keycloak_container, config.keycloak, debug)
        ),
        threading.Thread(
            target=run_with_exception,
            args=(run_redis_container, config.redis, debug)
        )
    ]
    
    for thread in threads:
        thread.start()
    
    for thread in threads:
        thread.join()
    
    if exceptions:
        raise ExceptionGroup("Container startup failed", exceptions)


@app.command(help="Stops running containers.")
def stop(
    debug: bool = False
):
    kc_container_manager = get_keycloak_container_manager(config.keycloak, debug)
    kc_container_manager.stop()

    redis_container_manager = get_redis_container_manager(config.redis, debug)
    redis_container_manager.stop()


@app.command(help="Stops and removes containers and their volumes.")
def remove(
    debug: bool = False
):
    kc_container_manager = get_keycloak_container_manager(config.keycloak, debug)
    kc_container_manager.remove()

    redis_container_manager = get_redis_container_manager(config.redis, debug)
    redis_container_manager.remove()


if __name__ == "__main__":
    app()
