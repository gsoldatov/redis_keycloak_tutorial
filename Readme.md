# Description
An implementation of a [Twitter clone](https://redis.io/docs/latest/develop/clients/patterns/twitter-clone/) project from Redis docs 
using Python 3.13, FastAPI, Redis as a database and Keycloak as a separate auth service.

Contains a simple API for registering & authenticating users, following other users, adding and viewing posts, as well as users' feeds.


# Running in Development Mode
1. Create virtual environment & install dependencies.

```bash
python -m venv venv --prompt "Redis + Keycloak tutorial"
source venv/bin/activate
pip install -r requirements.txt
```

2. Add a project configuration file `config.yml` (see `config.yml.example`).

3. Initialize Keycloak & Redis containers.

```bash
python src/container_cli.py run
```

4. Start development server.

```bash
fastapi dev src/app/main.py
```


# Running tests
Tests are implemented with Pytest + xdist plugin and use development containers for creating temporary Redis databases & Keycloak realms.

Tests can be run using tests module.

```bash
# Run all tests
python -m tests

# Run tests in tests/tests/validation dir
python -m tests validation
```

Each test file is executable and can be run on its own.


# Other
## Container Management
Keycloak and Redis containers can be created, started, stopped and removed with container CLI utility:

```bash
# Run or start existing containers
python src/container_cli.py run

# Stop existing containers
python src/container_cli.py stop

# Remove existing containers
python src/container_cli.py remove
```
