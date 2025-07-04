# Aletheia_v3/core/custom_acquisitions.py

import math

# This module provides heuristic functions that can be used to modify
# the objective function landscape for Bayesian Optimization. The goal is
# to guide the optimizer towards regions of the search space that are
# heuristically more likely to yield interesting ABC triples.

# Heuristics to guide Bayesian Optimization by adding a bonus to the objective function.
# The idea is to favor numbers 'a' and 'b' that are 'close' to powers of small primes,
# as these are often components of interesting ABC triples.

SMALL_PRIMES_FOR_HEURISTIC = [
    2,
    3,
    5,
    7,
    11,
    13,
]  # Tunable list of small primes
MAX_POWER_FOR_HEURISTIC = (
    40  # Max power to check (e.g., up to prime^40), tunable
)
# Cache for powers of small primes: {(prime, limit_exponent): [p^1, p^2, ...]}
# limit_exponent is roughly log_prime(value_upper_bound)
PRIME_POWER_SERIES_CACHE = {}


def _get_prime_power_series(prime: int, value_upper_bound: int) -> list[int]:
    """
    Generates and caches a series of prime^i terms that are
    less than or approximately equal to value_upper_bound.
    """
    if prime <= 1 or value_upper_bound < prime:
        return []

    # Determine the maximum exponent needed based on the value_upper_bound
    # prime^exponent <= value_upper_bound  => exponent * log(prime) <= log(value_upper_bound)
    # exponent <= log(value_upper_bound) / log(prime)
    limit_exponent = 0
    if (
        value_upper_bound > 1 and prime > 1
    ):  # Avoid log(1) or log_anything(1) if value_upper_bound is 1
        try:
            limit_exponent = (
                int(math.log(value_upper_bound, prime)) + 2
            )  # +2 for some margin
        except (
            ValueError
        ):  # math domain error if value_upper_bound or prime is invalid for log
            return []

    # Cap the exponent to avoid excessively long series for small primes
    effective_max_exponent = min(MAX_POWER_FOR_HEURISTIC, limit_exponent)

    cache_key = (prime, effective_max_exponent)
    if cache_key in PRIME_POWER_SERIES_CACHE:
        return PRIME_POWER_SERIES_CACHE[cache_key]

    series = []
    current_power = prime
    for _ in range(1, effective_max_exponent + 1):
        if (
            current_power > value_upper_bound * 1.5
        ):  # Check slightly beyond to catch near misses, but not too far
            # (e.g. if value is 100, prime is 2, series up to 128 is fine, but not 256 if not needed)
            break
        series.append(current_power)

        # Check for potential overflow before multiplication if numbers are huge
        # Though Python handles large integers, this is a safeguard.
        if (
            value_upper_bound / prime < current_power and prime > 1
        ):  # Avoid overflow for current_power * prime
            break
        current_power *= prime
        if current_power == 0:  # Should not happen with prime > 1
            break

    PRIME_POWER_SERIES_CACHE[cache_key] = series
    return series


def get_structural_bonus(
    value: int,
    bonus_scale_factor: float = 0.05,
    proximity_penalty_factor: float = 5.0,
    exact_match_multiplier: float = 2.0,
) -> float:
    """
    Calculates a bonus if 'value' is exactly a power of a small prime,
    or close to one. The bonus is higher for exact matches.

    The idea is that numbers with simple prime power structures (or close to them)
    might be more "interesting" components for ABC triples.

    @param value: The integer value (e.g., 'a' or 'b').
    @param bonus_scale_factor: Base magnitude of the bonus.
    @param proximity_penalty_factor: Controls how quickly the bonus decays with distance from a prime power.
    @param exact_match_multiplier: Multiplier for the bonus if 'value' is an exact prime power.
    @returns: A float bonus value (typically >= 0).
    """
    if not isinstance(value, int) or value <= 1:
        return 0.0

    min_relative_distance = float("inf")
    is_exact_power = False

    for p in SMALL_PRIMES_FOR_HEURISTIC:
        # Optimization: if p itself is already > value, no power of p can be close or equal
        if p > value and not (p == value):  # if p==value, it's p^1
            if (
                value * 0.5 > p
            ):  # if p is much larger than value, skip. Heuristic.
                continue

        power_series = _get_prime_power_series(p, value)
        if not power_series:
            if p == value:  # value is p^1
                is_exact_power = True
                min_relative_distance = 0.0
                break
            else:
                continue

        for pv_idx, pv in enumerate(power_series):
            if pv == value:
                is_exact_power = True
                min_relative_distance = 0.0
                break  # Found exact match for this prime p

            # Relative distance: abs(value - pv) / pv
            # This measures how far 'value' is from 'pv', relative to 'pv's size.
            distance = abs(value - pv)
            relative_distance = (
                distance / pv if pv > 0 else float("inf")
            )  # Should not be pv=0

            if relative_distance < min_relative_distance:
                min_relative_distance = relative_distance

        if is_exact_power:
            break  # Found exact match, no need to check other small primes

    final_bonus = 0.0
    if is_exact_power:
        final_bonus = bonus_scale_factor * exact_match_multiplier
    elif min_relative_distance != float("inf"):
        # Bonus decreases exponentially with relative distance
        final_bonus = bonus_scale_factor * math.exp(
            -proximity_penalty_factor * min_relative_distance
        )
        # Threshold small bonuses to avoid noise
        if final_bonus < (
            bonus_scale_factor * 0.01
        ):  # e.g. less than 1% of base bonus
            final_bonus = 0.0

    return final_bonus


if __name__ == "__main__":
    # Example Usage and Testing
    print(
        f"Bonus for 32 (2^5): {get_structural_bonus(32)}"
    )  # Expect higher bonus
    print(
        f"Bonus for 27 (3^3): {get_structural_bonus(27)}"
    )  # Expect higher bonus
    print(
        f"Bonus for 25 (5^2): {get_structural_bonus(25)}"
    )  # Expect higher bonus

    print(f"Bonus for 31 (near 32): {get_structural_bonus(31)}")
    print(f"Bonus for 33 (near 32): {get_structural_bonus(33)}")

    print(f"Bonus for 60 (near 64=2^6 or 55=5*11): {get_structural_bonus(60)}")
    print(
        f"Bonus for 100 (10^2, not prime power): {get_structural_bonus(100)}"
    )  # Will be low unless 100 is close to e.g. 3^4=81 or 5^3=125
    # Or if we extend SMALL_PRIMES_FOR_HEURISTIC to include 10 (not prime)
    # Or if code was changed to look for N*p^k etc.
    # Currently, only p^k.
    print(
        f"Bonus for 999 (near 1000=10^3 or other powers): {get_structural_bonus(999)}"
    )
    print(
        f"Bonus for a prime like 17: {get_structural_bonus(17)}"
    )  # Bonus for being 17^1
    print(f"Bonus for a prime like 19: {get_structural_bonus(19)}")
    print(f"Bonus for (2^30): {get_structural_bonus(2**30)}")
    print(f"Bonus for (2^30 -1): {get_structural_bonus(2**30 - 1)}")

    # Test _get_prime_power_series directly
    # PRIME_POWER_SERIES_CACHE.clear()
    # print(f"Powers of 2 up to 100: {_get_prime_power_series(2, 100)}")
    # print(f"Powers of 3 up to 100: {_get_prime_power_series(3, 100)}")
    # print(f"Powers of 17 up to 100: {_get_prime_power_series(17, 100)}")
    # print(f"Powers of 97 up to 100: {_get_prime_power_series(97, 100)}")
    # print(f"Powers of 101 up to 100: {_get_prime_power_series(101, 100)}") # Empty
    # print(f"Cache after: {PRIME_POWER_SERIES_CACHE}")
