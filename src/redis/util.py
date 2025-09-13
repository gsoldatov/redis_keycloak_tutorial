class RedisKeys:
    @staticmethod
    def user(username: str) -> str:
        return f"user:{username}"