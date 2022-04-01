'''
Tests
'''
from trouble import clear, flip_card, is_double_trouble, is_trouble_double, is_empty

def test_simple():
    clear()
    flip_card({
        'suit': 'Hearts',
        'number': '9',
    })
    flip_card({
        'suit': 'Clubs',
        'number': '9',
    })
    assert not is_trouble_double()
    assert not is_empty()
    assert is_double_trouble()

# Write your tests here
