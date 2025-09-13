from pydantic import BaseModel, Field, ConfigDict, EmailStr, model_validator
from typing import Annotated, Self


Username = Annotated[str, Field(min_length=8, max_length=32)]
Password = Annotated[str, Field(min_length=8, max_length=32)]
Name = Annotated[str, Field(min_length=1, max_length=64)]


class Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class UserCredentials(Base):
    """ Login route request body schema. """
    username: Username
    password: Password


class User(Base):
    """ Public attributes of a user. """
    username: Username
    first_name: Name
    last_name: Name


class UserPublic(User):
    """ Public attributes of a user. """
    model_config = ConfigDict(extra="ignore")


class UserWithID(User):
    user_id: str


class UserRegistrationCredentials(User):
    """ Registration route request body schema. """
    password: Password
    password_repeat: Password
    email: EmailStr

    @model_validator(mode="after")
    def validate_password_repeat(self) -> Self:
        if self.password != self.password_repeat:
            raise ValueError("Passwords do not match")
        return self
