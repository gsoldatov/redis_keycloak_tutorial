class AuthGenerator:
    def get_login_credentials_request_body(
        self,
        username: str = "username",
        password: str = "password"
    ):
        return {"username": username, "password": password}
        

class DataGenerator:
    def __init__(self):
        self.auth = AuthGenerator()
