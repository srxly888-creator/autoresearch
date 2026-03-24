from __future__ import annotations


def is_prime(value: int) -> bool:
    if value < 2:
        return False
    for factor in range(2, int(value ** 0.5) + 1):
        if value % factor == 0:
            return False
    return True


def count_twin_primes(limit: int) -> int:
    twin_count = 0
    previous_prime = None
    for candidate in range(2, limit + 1):
        if not is_prime(candidate):
            continue
        if previous_prime is not None and candidate - previous_prime == 2:
            twin_count += 1
        previous_prime = candidate
    return twin_count
