import pytest

import os
import sys

# Dodaje folder nadrzędny (tam, gdzie jest logic.py) do ścieżki Pythona
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic import (
    is_palindrome,
    fibonacci,
    count_vowels,
    calculate_discount,
    flatten_list,
    word_frequencies,
    is_prime
)


# 1. is_palindrome
@pytest.mark.parametrize("text, expected", [
    ("kajak", True),
    ("Kobyła ma mały bok", True),
    ("python", False),
    ("", True),
    ("A", True),
])
def test_is_palindrome(text, expected):
    assert is_palindrome(text) == expected


# 2. fibonacci
@pytest.mark.parametrize("n, expected", [
    (0, 0),
    (1, 1),
    (5, 5),
    (10, 55),
])
def test_fibonacci_valid(n, expected):
    assert fibonacci(n) == expected


def test_fibonacci_negative():
    with pytest.raises(ValueError):
        fibonacci(-1)


# 3. count_vowels
@pytest.mark.parametrize("text, expected", [
    ("Python", 2),
    ("AEIOUY", 6),
    ("bcd", 0),
    ("", 0),
    ("Próba żółwia", 3),
])
def test_count_vowels(text, expected):
    assert count_vowels(text) == expected


# 4. calculate_discount
@pytest.mark.parametrize("price, discount, expected", [
    (100, 0.2, 80.0),
    (50, 0, 50.0),
    (200, 1, 0.0),
])
def test_calculate_discount_valid(price, discount, expected):
    assert calculate_discount(price, discount) == expected


@pytest.mark.parametrize("price, discount", [
    (100, -0.1),
    (100, 1.5),
])
def test_calculate_discount_invalid(price, discount):
    with pytest.raises(ValueError):
        calculate_discount(price, discount)


# 5. flatten_list
@pytest.mark.parametrize("nested, expected", [
    ([1, 2, 3], [1, 2, 3]),
    ([1, [2, 3], [4, [5]]], [1, 2, 3, 4, 5]),
    ([], []),
    ([[[1]]], [1]),
    ([1, [2, [3, [4]]]], [1, 2, 3, 4]),
])
def test_flatten_list(nested, expected):
    assert flatten_list(nested) == expected


# 6. word_frequencies
@pytest.mark.parametrize("text, expected", [
    ("To be or not to be", {"to": 2, "be": 2, "or": 1, "not": 1}),
    ("Hello, hello!", {"hello": 2}),
    ("", {}),
    ("Python Python python", {"python": 3}),
])
def test_word_frequencies_basic(text, expected):
    assert word_frequencies(text) == expected


def test_word_frequencies_punctuation():
    text = "Ala ma kota, a kot ma Ale."
    result = word_frequencies(text)
    assert result["ala"] == 1
    assert result["ma"] == 2
    assert result["kot"] == 1
    assert result["kota"] == 1
    assert result["ale"] == 1


# 7. is_prime
@pytest.mark.parametrize("n, expected", [
    (2, True),
    (3, True),
    (4, False),
    (0, False),
    (1, False),
    (5, True),
    (97, True),
])
def test_is_prime(n, expected):
    assert is_prime(n) == expected
