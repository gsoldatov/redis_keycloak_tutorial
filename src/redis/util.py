from typing import cast

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
    
    @staticmethod
    def access_token(access_token: str) -> str:
        return f"access_token:{access_token}"

    next_post_id = "next_post_id"


def get_post_id_mapping(post_ids: list[int] | list[str] | int | str):
    """ Returns a mapping for provided `post_ids` to be inserted into a sorted set. """
    if not isinstance(post_ids, list):
        post_ids = [post_ids]   # type: ignore
    post_ids = cast(list[int] | list[str], post_ids)
    return {str(post_id): -int(post_id) for post_id in post_ids}
