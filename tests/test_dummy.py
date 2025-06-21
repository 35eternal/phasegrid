print("Starting test_dummy.py")

def test_dummy():
    print("Running test_dummy")
    assert True
    print("test_dummy passed!")

def test_basic_math():
    print("Running test_basic_math")
    assert 1 + 1 == 2
    print("test_basic_math passed!")

if __name__ == "__main__":
    print("Running tests...")
    test_dummy()
    test_basic_math()
    print("All tests passed!")
