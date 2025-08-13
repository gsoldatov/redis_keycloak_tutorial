import os


def run_pytest_tests(file: str | os.PathLike):
    """Runs pytest tests in the provided `file`"""
    os.system(f'pytest "{os.path.abspath(file)}" -v')
    # os.system(f'pytest "{os.path.abspath(file)}" -v --asyncio-mode=auto')
