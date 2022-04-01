from filter import filter_string
import pytest

def test_1():
    assert(filter_string("Hello, my name is Mr O'Toole.") == "Hello my name is mr otoole")

def test_basic():
    assert(filter_string("Hello my name IS Lil'Wuyn") == "Hello my name is lilwuyn")

def test_punch_at_head():
    assert(filter_string("!!!Hello, my name is Mr O'Toole.") == "Hello my name is mr otoole")

def test_contains_number():
    with pytest.raises(ValueError):
        filter_string("Hello, my name is 007 Mr O'Toole.")
        filter_string("555 Hello, my name is 007 Mr O'Toole.")