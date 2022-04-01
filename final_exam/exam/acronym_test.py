from _pytest.python_api import raises
from acronym import acronym_make
import pytest

def test_basic():
    assert acronym_make(['I am very tired today']) == ['VTT']
    assert acronym_make(['Why didnt I study for this exam more', 'I dont know']) == ['WDSFTM', 'DK']
    assert acronym_make(['Phan Tuan Kiet', 'I dont know']) == ['PTK', 'DK']

def test_error():
    with pytest.raises(ValueError):
        acronym_make([])

def test_all_vowel():
    assert acronym_make(['I am an elephant']) == ['']

def test_long_string():
    assert acronym_make(['Pass Pass Pass Pass Pass Pass Pass Pass Pass Pass Pass Pass', 'I dont know']) == ['N/A', 'DK']