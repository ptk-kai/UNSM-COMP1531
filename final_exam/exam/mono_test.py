from mono import monotonic

def test_1():
    data = [(1,3,2),(1,2)]
    out = ['neither', 'monotonically increasing']
    assert monotonic(data) == out

