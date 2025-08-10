import subprocess


def run_subprocess(args: list[str]):
    try:
        result = subprocess.run(
            args,
            check=True,
            capture_output=True,
            text=True
        )
        if not result:
            raise RuntimeError(f"Failed to get subprocess result for command:\n{args}")
        return result
    except subprocess.CalledProcessError as e:
            print(e.stdout)
            print(e.stderr)
            raise


class ContainerManager:
    """ Utility class with common container management functions. """
    def __init__(
            self, 
            name: str,
            run_args: list[str],
            image: str,
            run_command_args: list[str],
            debug: bool
        ):
        self.name = name
        """ Container name. """
        self.run_args = run_args
        """
        List of arg names & values for `docker run` command
        (mapped ports, env variables, volumes, etc.).
        """
        self.image = image
        """ Image name of the container. """
        self.run_command_args = run_command_args
        """ Additional args passed to the container. """
        self._debug = debug
    
    def print_debug(self, msg: str):
        if self._debug:
            print(f"{self.name} > {msg}")
    
    def exists(self) -> bool:
        """ Check if the container exists. """
        result = run_subprocess([
            "docker", "ps", 
            "-a",   # show stopped containers as well
            "--filter", f"name={self.name}"
        ])
        stdout_lines = result.stdout.split("\n")
        exists = len(stdout_lines) > 1 and len(stdout_lines[1]) > 0
        self.print_debug(f"Container exists: {exists}.")
        return exists 

    def is_running(self) -> bool:
        """ Check if the container is running. """
        result = run_subprocess([
            "docker", "ps", 
            "--filter", f"name={self.name}", 
            "--format", "{{.Status}}"
        ])
        is_running = "Up" in result.stdout
        self.print_debug(f"Container is running: {is_running}.")
        return is_running

    def run(self) -> None:
        """
        Start a PostgreSQL container with specified configuration,
        if it's not running.
        """
        # Start an existing container
        if self.exists():
            if not self.is_running():
                run_subprocess(["docker", "start", self.name])
                self.print_debug("Started an existing container.")
            else:
                self.print_debug("Container is already running.")
        
        # Create a new container
        else:
            args: list[str] = [
                "docker", "run",
                "--name", self.name,
                "-d"
            ] + self.run_args + [self.image] + self.run_command_args
            
            run_subprocess(args)
            self.print_debug("Created & started a new container.")

    def stop(self) -> None:
        """Stop the PostgreSQL container if it's running."""
        run_subprocess(["docker", "stop", self.name])
        self.print_debug("Stopped the container.")
    
    def remove(self) -> None:
        """ Remove the PostgreSQL container and its volume. """
        run_subprocess([
            "docker", "rm",
            "--force", "--volumes",
            self.name
        ])
        self.print_debug("Removed the container.")
