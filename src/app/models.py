from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, EmailStr, model_validator, \
    PlainValidator, PlainSerializer
from typing import Annotated, Self, Any


Username = Annotated[str, Field(min_length=8, max_length=32)]
Password = Annotated[str, Field(min_length=8, max_length=32)]
Name = Annotated[str, Field(min_length=1, max_length=64)]
PaginationCursor = Annotated[int, Field(ge=0, le=2**31 - 1)]
PostID = Annotated[int, Field(ge=1, le=2**31 - 1)]

# Datetime
def validate_datetime(value: Any) -> datetime:
    """
    Custom validator for the `Datetime` type, which allows ISO-formatted strings.
    """
    if isinstance(value, datetime): return value
    elif isinstance(value, str): return datetime.fromisoformat(value)
    else: raise ValueError("Input should be a valid datetime")


Datetime = Annotated[
    datetime,
    # Field(strict=False),    # allow converting from strings 
    #                         # (NOTE: this does not work in type unions with strict mode enabled)
    PlainValidator(validate_datetime),
    PlainSerializer(lambda x: x.isoformat(), when_used="always")
]


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


class NewPost(Base):
    content: str = Field(min_length=1, max_length=1000)

class Post(NewPost):
    created_at: Datetime
    author: Username


class PostWithID(Post):
    post_id: PostID
