"""
POST /users/:username/posts route validation tests.
"""
if __name__ == "__main__":
    import os, sys
    sys.path.insert(0, os.path.abspath(os.path.join(__file__, "../" * 4)))
    from tests.util import run_pytest_tests

from pydantic import BaseModel, ValidationError
import pytest

from src.app.models import NewPost
from tests.data_generators import DataGenerator


def test_incorrect_values(
    data_generator: DataGenerator
):
    # Missing attributes
    for attr in ("content",):
        post = data_generator.posts.new_post_request_body()
        post.pop(attr)
        with pytest.raises(ValidationError):
            NewPost.model_validate(post)
    
    # Unallowed attributes
    post = data_generator.posts.new_post_request_body()
    post["unallowed"] = "value"
    with pytest.raises(ValidationError):
        NewPost.model_validate(post)
    
    # Incorrect attribute values
    incorrect_values = {
        "content": [None, False, 1, [], {}, "", "a" * 1001]
    }
    for attr in incorrect_values:
        for value in incorrect_values[attr]:
            post = data_generator.posts.new_post_request_body()
            post[attr] = value
            with pytest.raises(ValidationError):
                NewPost.model_validate(post)


def test_correct_values():
    for post in [
        {"content": "a"}, {"content": "a" * 1000}
    ]:
        NewPost.model_validate(post)


if __name__ == "__main__":
    run_pytest_tests(__file__) # type: ignore[reportPossiblyUnboundVariable]
