# core/domain.py
import math
from dataclasses import dataclass
from functools import lru_cache

from cypari2 import Pari # For PARI/GP integration
pari = Pari() # Initialize PARI/GP instance

# Numba for JIT compilation - will be used where appropriate
# import numba

def gcd(a: int, b: int) -> int:
    """
    Computes the greatest common divisor (GCD) of two integers a and b
    using PARI/GP via cypari2.

    @param a: The first integer.
    @param b: The second integer.
    @returns: The greatest common divisor of a and b.
    """
    # PARI's gcd is very efficient and handles large numbers.
    # It returns a PARI GEN object, so convert to Python int.
    return int(pari.gcd(a, b))

@dataclass(frozen=True)
class ABCTriple:
    a: int
    b: int
    c: int

@dataclass(frozen=True)
class ABCQuality:
    triple: ABCTriple
    quality: float

def get_quality(a: int, b: int) -> float:
    """
    Calculates the quality 'q' for a potential abc-triple (a, b, c=a+b).

    The quality 'q' is a measure of how "surprising" or "exceptional" a triple is
    in the context of the abc conjecture. It relates the magnitude of c to the
    product of its distinct prime factors (the radical of abc).

    @equations:
        The abc conjecture states that for any epsilon > 0, there are only finitely
        many triples (a, b, c) of coprime positive integers with a + b = c such that
        c > rad(abc)^(1+epsilon).

        The quality q is defined as:
        q(a,b,c) = log(c) / log(rad(a*b*c))
        where rad(n) is the radical of n, i.e., the product of the distinct prime
        factors of n.
        rad(n) = product_{p|n, p prime} p

    @references:
        1. Oesterlé, J. (1988). "Nouvelles approches du 'théorème' de Fermat".
           Séminaire Bourbaki, Vol. 1987/88, Astérisque No. 161-162, exp. no. 694, pp. 165-186.
        2. Masser, D. W. (1985). "Open problems". Proceedings of the Symposium on
           Analytic Number Theory. London: Imperial College.

    @param a: The first term of the potential triple. Must be a positive integer.
    @param b: The second term of the potential triple. Must be a positive integer.
    @returns: The quality 'q' of the triple (a, b, a+b). Returns 0.0 if:
              - a or b is not positive.
              - a and b are not coprime (gcd(a,b) != 1).
              - a >= b (to ensure uniqueness and avoid redundant checks, as (a,b,c) and (b,a,c) are equivalent for quality calculation after ordering).
              - rad(abc) >= c (which implies q <= 1 or is undefined if rad=0 or 1).
              - rad(abc) = 0 (should not happen with positive a,b,c).
    """
    if not (isinstance(a, int) and isinstance(b, int) and a > 0 and b > 0):
        return 0.0
    if a >= b: # Ensure a < b for uniqueness, though quality is symmetric for a,b
        return 0.0
    if gcd(a, b) != 1:
        return 0.0

    c = a + b

    # Cache results of _radical to avoid re-computation for the same number
    @lru_cache(maxsize=1024) # Adjust maxsize based on expected unique numbers
    def _radical(n_val: int) -> int:
        """
        Computes the radical (square-free kernel) of an integer 'n' using PARI/GP (via cypari2)
        for prime factorization. The radical of 'n' is the product of its distinct prime factors.
        This function is cached using functools.lru_cache.

        Example: rad(72) = rad(2^3 * 3^2) = 2 * 3 = 6.

        @param n_val: The integer for which to compute the radical.
        @returns: The radical of n_val. Returns 0 if n_val is 0, 1 if n_val is +/-1.
        """
        if n_val == 0:
            return 0
        if abs(n_val) == 1:
            return 1

        try:
            # pari.factor() returns a Factorization object (matrix-like).
            # Column 0 contains prime factors, Column 1 contains their exponents.
            # Example: pari.factor(72) -> [2, 3; 3, 2] (means 2^3 * 3^2)
            factors_matrix = pari.factor(abs(n_val))

            # The distinct prime factors are in the first column of the matrix.
            distinct_primes = factors_matrix[0]

            # Calculate the product of these distinct primes.
            radical_val = 1
            if len(distinct_primes) > 0: # Check if there are any prime factors
                for p in distinct_primes:
                    radical_val *= int(p) # Convert PARI prime to int before multiplying
            else: # Should not happen for abs(n_val) > 1
                radical_val = abs(n_val) if abs(n_val) > 1 else 1


            return radical_val
        except Exception as e:
            # Handle potential errors from PARI/GP, though it's robust.
            # This might occur for extremely large numbers beyond PARI's limits or config.
            # For now, re-raise or log, or fall back to a simpler method if critical.
            print(f"Error during PARI/GP factorization of {n_val}: {e}")
            # As a fallback, could use a simple Python version, but it would be slow.
            # For now, let it propagate or return a value indicating error.
            raise # Or return a specific error indicator if preferred by calling logic

    rad_abc = _radical(a * b * c)

    if rad_abc == 0 or rad_abc >= c : # log(rad_abc) would be undefined or quality <=1 or rad_abc is 0
        return 0.0

    # Ensure rad_abc is not 1 if c > 1 to avoid log(1)=0 in denominator
    if rad_abc == 1 and c > 1:
        return 0.0 # Only if a=1, b=1, c=2, rad(2)=2. This case is fine.
                   # If a*b*c = 1, then a=1, b=0 (not allowed) or a=1, b=1, c=2.
                   # If a=1, b=1, then gcd(1,1)=1. c=2. rad(1*1*2)=2. log(2)/log(2) = 1.
                   # This check is more about rad_abc being a meaningful divisor.

    try:
        quality = math.log(c) / math.log(rad_abc)
    except ValueError: # Should be caught by rad_abc >= c or rad_abc == 0
        return 0.0

    return quality
