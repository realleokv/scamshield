"""Small dependency-free Base58 decoder. No curve check: PDAs are valid addresses."""
ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


def valid_base58(value, size):
    if not isinstance(value, str) or not 1 <= len(value) <= (44 if size == 32 else 88):
        return False
    n = 0
    for ch in value:
        if ch not in ALPHABET:
            return False
        n = n * 58 + ALPHABET.index(ch)
    zeros = len(value) - len(value.lstrip('1'))
    return zeros + (n.bit_length() + 7) // 8 == size


def valid_address(value):
    return valid_base58(value, 32)


def valid_signature(value):
    return valid_base58(value, 64)


def valid_time(value):
    # Unix timestamps in years 2000–2100; do not coerce booleans or strings.
    return type(value) is int and 946684800 <= value <= 4102444800

