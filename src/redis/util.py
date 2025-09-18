class RedisKeys:
    @staticmethod
    def user(username: str) -> str:
        return f"user:{username}"
    
    @staticmethod
    def user_followers(username: str) -> str:
        return f"user_followers:{username}"
    
    @staticmethod
    def user_posts(username: str) -> str:
        return f"user_posts:{username}"
    
    @staticmethod
    def user_feed(username: str) -> str:
        return f"user_feed:{username}"
    
    @staticmethod
    def post(post_id: str | int) -> str:
        return f"post:{post_id}"

    next_post_id = "next_post_id"
