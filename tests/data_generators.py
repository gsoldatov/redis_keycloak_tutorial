from datetime import datetime, timezone

from src.app.models import UserWithID, PostWithID


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
    
    def get_bearer_header_with_invalid_token(self) -> dict:
        return {"Authorization": f"Bearer {_INVALID_ACCESS_TOKEN}"}


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


class PostsGenerator:
    def post(
        self,
        post_id: int = 1,
        created_at: datetime | None = None,
        content: str = "post content",
        author: str = "username"
    ) -> PostWithID:
        created_at = created_at if created_at is not None else datetime.now(tz=timezone.utc)

        return PostWithID(
            post_id=post_id,
            created_at=created_at,
            content=content,
            author=author
        )

class DataGenerator:
    def __init__(self):
        self.auth = AuthGenerator()
        self.users = UsersGenerator()
        self.posts = PostsGenerator()


_INVALID_ACCESS_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICI3dDJIRmdvbGNhU203b1ppekd2S0Y0MGNiZXJ4YUw1UFNhek4tRFBrdmo0In0.eyJleHAiOjE3NTc5NDIzODgsImlhdCI6MTc1Nzk0MjA4OCwianRpIjoib25ydHJvOmQzOGU5NGZkLTE2ZjMtZTlkZC1lMmM5LWNkMDY1NWYzMjk1NiIsImlzcyI6Imh0dHA6Ly9sb2NhbGhvc3Q6MTUwODAvcmVhbG1zL3Rlc3RfYmMzYTg0MTgwOTk3NDFjNDlmOGQ0ZWY5YmIwMGRkZDkiLCJhdWQiOiJhY2NvdW50Iiwic3ViIjoiODVmYWJlODgtNmY5OS00Y2QxLTljMzQtOGVlNWJjMzUwMWRlIiwidHlwIjoiQmVhcmVyIiwiYXpwIjoiYXBwX2NsaWVudCIsInNpZCI6IjUyMWQ1OTYyLTIyODUtNGEyYS04ZGEzLTIzYjMxM2U3NDAwOCIsImFjciI6IjEiLCJyZWFsbV9hY2Nlc3MiOnsicm9sZXMiOlsib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiIsImRlZmF1bHQtcm9sZXMtdGVzdF9iYzNhODQxODA5OTc0MWM0OWY4ZDRlZjliYjAwZGRkOSJdfSwicmVzb3VyY2VfYWNjZXNzIjp7ImFjY291bnQiOnsicm9sZXMiOlsibWFuYWdlLWFjY291bnQiLCJtYW5hZ2UtYWNjb3VudC1saW5rcyIsInZpZXctcHJvZmlsZSJdfX0sInNjb3BlIjoib3BlbmlkIHByb2ZpbGUgZW1haWwiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwibmFtZSI6InVzZXJuYW1lIGZpcnN0IG5hbWUgdXNlcm5hbWUgbGFzdCBuYW1lIiwicHJlZmVycmVkX3VzZXJuYW1lIjoidXNlcm5hbWUiLCJnaXZlbl9uYW1lIjoidXNlcm5hbWUgZmlyc3QgbmFtZSIsImZhbWlseV9uYW1lIjoidXNlcm5hbWUgbGFzdCBuYW1lIiwiZW1haWwiOiJ1c2VybmFtZUBleGFtcGxlLmNvbSJ9.EguBV48lxX8L_p80WanQae9HigQd7v6IKnZv_cMt1dZqkQe_G-KGGy_tWi_W-3VDOApurxRKw9dJVz-piS8ROPBB-gzxvxcRP3eN11lBA6LWW1n51b2hdCHAvdQm39tllQiAVqfNH8eRr7RixMgQL9nDjGTzTkGPoi4YGN3W2TcFZITjR0rEYlhXnHTdEfCvwYLXjH6udvE_Zz_NbVC6tLuxTejpOtyrhnQvJofTKTSBcRdjcDiKz9tuQ_CIoESz9wHN4F7hzmZ-XmDzj671lTId8y_08OQS0MRGwo49ptV_jhQ1BY6SPLfzhAbnUa_Q74EysT3hkKOOh4nQ6pkGEQ"
""" Invalid access token of correct structure """
_DECODED_INVALID_ACCESS_TOKEN = {'exp': 1757942388, 'iat': 1757942088, 'jti': 'onrtro:d38e94fd-16f3-e9dd-e2c9-cd0655f32956', 'iss': 'http://localhost:15080/realms/test_bc3a8418099741c49f8d4ef9bb00ddd9', 'aud': 'account', 'sub': '85fabe88-6f99-4cd1-9c34-8ee5bc3501de', 'typ': 'Bearer', 'azp': 'app_client', 'sid': '521d5962-2285-4a2a-8da3-23b313e74008', 'acr': '1', 'realm_access': {'roles': ['offline_access', 'uma_authorization', 'default-roles-test_bc3a8418099741c49f8d4ef9bb00ddd9']}, 'resource_access': {'account': {'roles': ['manage-account', 'manage-account-links', 'view-profile']}}, 'scope': 'openid profile email', 'email_verified': True, 'name': 'username first name username last name', 'preferred_username': 'username', 'given_name': 'username first name', 'family_name': 'username last name', 'email': 'username@example.com'}
""" Decoded _INVALID_ACCESS_TOKEN """