import os

def load_tests(loader, standard_tests, pattern):
    """
    Discover and load all test modules from the current directory and its subdirectories.
    The tests are loaded from files that match the given pattern.
    
    Parameters:
    - loader: A unittest.TestLoader object used to load tests.
    - standard_tests: The standard tests that are initially present. This function will add the discovered tests to this suite.
    - pattern: A string pattern to match the test files. Typically, this would be 'test_*.py' to match all Python files starting with 'test_'.
    
    Returns:
    - A unittest.TestSuite object containing all the loaded tests.
    """
    this_dir = os.path.dirname(__file__)
    package_tests = loader.discover(start_dir=this_dir, pattern='test_*')
    standard_tests.addTests(package_tests)
    return standard_tests
