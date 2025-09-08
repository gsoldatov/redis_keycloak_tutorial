from pydantic import BaseModel, Field, ConfigDict, EmailStr, model_validator
from typing import Annotated, Self


Username = Annotated[str, Field(min_length=8, max_length=32)]
Password = Annotated[str, Field(min_length=8, max_length=32)]
Name = Annotated[str, Field(min_length=1, max_length=64)]

class UserCredentials(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: Username
    password: Password


class UserRegistrationCredentials(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: Username
    password: Password
    password_repeat: Password
    email: EmailStr
    first_name: Name
    last_name: Name

    @model_validator(mode="after")
    def validate_password_repeat(self) -> Self:
        if self.password != self.password_repeat:
            raise ValueError("Passwords do not match")
        return self
