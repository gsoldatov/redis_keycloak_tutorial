"""
Wrapper over pytest for running multiple test files.
"""
if __name__ == "__main__":
    import os, sys
    project_root = os.path.abspath(os.path.join(__file__, "..", ".."))
    sys.path.insert(0, project_root)

    # Get args for pytest
    args = " ".join(sys.argv[1:])

    # Change root dir
    cwd = os.getcwd()
    tests_dir = os.path.abspath(os.path.join(__file__, "..", "tests/"))
    os.chdir(tests_dir)

    # Run tests
    cmd = f'pytest -n auto --dist=loadfile {args}'

    os.system(cmd)
    
    # Restore current working directory
    os.chdir(cwd)
