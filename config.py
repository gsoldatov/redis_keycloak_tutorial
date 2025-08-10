from pathlib import Path
from pydantic import BaseModel, Field
import yaml


class KeycloakConfig(BaseModel):
    container_name: str = Field(min_length=1)
    container_main_port: int = Field(ge=1024, le=65535)
    container_healthcheck_port: int = Field(ge=1024, le=65535)

    max_healthcheck_retries: int = Field(ge=0)
    healthcheck_retry_timeout: float = Field(ge=0)

    admin_username: str = Field(min_length=1)
    admin_password: str = Field(min_length=1)

    app_realm_name: str = Field(min_length=1)
    app_client_id: str = Field(min_length=1)
    app_client_secret: str = Field(min_length=1)

    @property
    def keycloak_url(self) -> str:
        return f"http://localhost:{self.container_main_port}"
    
    @property
    def keycloak_healthcheck_url(self) -> str:
        return f"http://localhost:{self.container_healthcheck_port}/health/ready"


class Config(BaseModel):
    keycloak: KeycloakConfig


def load_config() -> Config:
    path = Path(__file__).parent / "config.yml"
    with open(path) as f:
        data = yaml.safe_load(f)
    return Config(**data)

