import filelock
import json
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field


_shared_test_state_file_dir = Path(__file__).parent / "tests"
_shared_test_state_file = _shared_test_state_file_dir / "shared_test_state.json"
_shared_test_state_file_lock = _shared_test_state_file_dir / "shared_test_state.json.lock"

lock = filelock.FileLock(_shared_test_state_file_lock, timeout=1)


class TestState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    testrun_uid: str
    last_used_redis_database_number: int = Field(ge=0)


class SharedTestStateManager:
    """ Class for managing shared test state stored in a file. """
    @lock
    def reset_state(self, testrun_uid: str) -> None:
        """
        Ensures shared state is reset on the first call during the test run
        (checks if shared state contains the same `testrun_uid` as provided
        (and the method should be provided with the corresponding pytest-xdist fixture))
        """
        default_state = TestState(
            testrun_uid=testrun_uid,
            last_used_redis_database_number=0
        )

        if not _shared_test_state_file.exists():
            self._write_state(default_state)
        else:
            current_state = self._read_state()
            if current_state.testrun_uid != testrun_uid:
                self._write_state(default_state)
    
    @lock
    def get_free_redis_database_number(self) -> int:
        """
        Returns the next free Redis database number
        and increments the corresponding state value
        """
        current_state = self._read_state()
        current_state.last_used_redis_database_number += 1
        self._write_state(current_state)
        return current_state.last_used_redis_database_number
    
    @lock
    def _read_state(self) -> TestState:
        """ Returns current test state. """
        with open(_shared_test_state_file) as file:
            return TestState.model_validate_json(file.read())
    
    @lock
    def _write_state(self, state: TestState) -> None:
        with open(_shared_test_state_file, mode="w") as file:
            file.write(state.model_dump_json())