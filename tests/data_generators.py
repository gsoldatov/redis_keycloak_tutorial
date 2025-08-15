class AuthGenerator:
    def get_login_credentials_request_body(
        self,
        username: str = "username",
        password: str = "password"
    ):
        return {"username": username, "password": password}
    
    def get_bearer_header(self, token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}
        

class DataGenerator:
    def __init__(self):
        self.auth = AuthGenerator()
