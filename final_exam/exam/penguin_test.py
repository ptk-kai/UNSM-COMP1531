from penguin import validate

def test_1():
    assert validate('P8464Q94944Z')

def test_2():
    assert validate('A1234B12344C')

def test_3():
    assert not validate('A1234567890B')
