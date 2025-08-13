from pydantic import BaseModel, Field, ConfigDict


class UserCredentials(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1)
    password: str = Field(min_length=1)
