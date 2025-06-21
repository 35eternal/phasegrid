@"
def test_dummy():
    '''This test always passes'''
    assert True
    
def test_basic_math():
    '''Basic math should work'''
    assert 1 + 1 == 2
"@ | Out-File -FilePath "tests\test_dummy.py" -Encoding utf8