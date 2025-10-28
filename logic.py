import re

def is_palindrome(text: str) -> bool:
    cleaned = ''.join(text.lower().split())
    return cleaned == cleaned[::-1]


def fibonacci(n: int) -> int:
    if n < 0:
        raise ValueError("n musi być liczbą nieujemną")
    if n == 0:
        return 0
    elif n == 1:
        return 1

    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


def count_vowels(text: str) -> int:
    vowels = set("aeiouy")
    return sum(1 for ch in text.lower() if ch in vowels)


def calculate_discount(price: float, discount: float) -> float:
    if not (0 <= discount <= 1):
        raise ValueError("Discount musi być w zakresie od 0 do 1.")
    return price * (1 - discount)


def flatten_list(nested_list: list) -> list:
    flat = []
    for item in nested_list:
        if isinstance(item, list):
            flat.extend(flatten_list(item))
        else:
            flat.append(item)
    return flat


def word_frequencies(text: str) -> dict:
    words = re.findall(r'\b\w+\b', text.lower())  # wydobycie słów
    frequencies = {}
    for word in words:
        frequencies[word] = frequencies.get(word, 0) + 1
    return frequencies


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(n**0.5) + 1, 2):
        if n % i == 0:
            return False
    return True


print(is_palindrome("kajak"))
print(fibonacci(7))
print(count_vowels("adrian"))
print(calculate_discount(100, 0.2))
print(flatten_list([1, [2, 3], [4, [5]]]))
print(word_frequencies("Lorum Ipsum Dolorosa lorum lOrUm"))
print(is_prime(5))

