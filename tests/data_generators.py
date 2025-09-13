from src.app.models import UserWithID


class AuthGenerator:
    def get_auth_register_request_body(
        self,
        email: str = "test@example.com",
        username: str = "username",
        first_name: str = "first name",
        last_name: str = "last name",
        password: str = "password",
        password_repeat: str | None = None,

    ):
        return {
            "email": email,
            "username": username,
            "password": password,
            "first_name": first_name,
            "last_name": last_name,
            "password_repeat": password_repeat if password_repeat is not None else password
        }
    
    def get_auth_login_request_body(
        self,
        username: str = "username",
        password: str = "password"
    ):
        return {"username": username, "password": password}
    
    def get_bearer_header(self, token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}


class UsersGenerator:
    def redis_user_data(
        self,
        user_id: str = "user id",
        username: str = "username",
        first_name: str = "first name",
        last_name: str = "last name"
    ) -> UserWithID:
        return UserWithID(
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        

class DataGenerator:
    def __init__(self):
        self.auth = AuthGenerator()
        self.users = UsersGenerator()
