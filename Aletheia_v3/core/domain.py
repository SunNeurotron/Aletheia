# Copyright 2025 Alant
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# core/domain.py
import logging  # Import logging module
import math
from dataclasses import dataclass
from functools import lru_cache

from cypari2 import Pari  # For PARI/GP integration

pari = Pari()  # Initialize PARI/GP instance

# Numba for JIT compilation - will be used where appropriate
# import numba

# Get a logger instance for this module
logger = logging.getLogger(__name__)


def gcd(a: int, b: int) -> int:
    """
    Computes the greatest common divisor (GCD) of two integers a and b
    using PARI/GP via cypari2.

    :param a: The first integer.
    :type a: int
    :param b: The second integer.
    :type b: int
    :return: The greatest common divisor of a and b.
    :rtype: int
    """
    # PARI's gcd is very efficient and handles large numbers.
    # It returns a PARI GEN object, so convert to Python int.
    return int(pari.gcd(a, b))


@dataclass(frozen=True)
class ABCTriple:
    """
    Represents an abc-triple (a, b, c) where a, b, c are positive integers,
    a and b are coprime, and a + b = c.
    """
    a: int
    b: int
    c: int


@dataclass(frozen=True)
class ABCQuality:
    """
    Represents an abc-triple along with its calculated quality 'q'.
    """
    triple: ABCTriple
    quality: float


def get_quality(a: int, b: int) -> float:
    """
    Calculates the quality 'q' for a potential abc-triple (a, b, c=a+b).

    The quality 'q' is a measure of how "surprising" or "exceptional" a triple is
    in the context of the abc conjecture. It relates the magnitude of c to the
    product of its distinct prime factors (the radical of abc).

    .. math::
        q(a,b,c) = \\frac{\\log(c)}{\\log(\\text{rad}(abc))}

    where :math:`\\text{rad}(n)` is the radical of n, i.e., the product of the distinct prime
    factors of n:

    .. math::
        \\text{rad}(n) = \\prod_{p|n, p \\text{ prime}} p

    The abc conjecture states that for any :math:`\\epsilon > 0`, there are only finitely
    many triples (a, b, c) of coprime positive integers with a + b = c such that
    :math:`c > \\text{rad}(abc)^{1+\\epsilon}`.

    References:
        1. Oesterlé, J. (1988). "Nouvelles approches du 'théorème' de Fermat".
           Séminaire Bourbaki, Vol. 1987/88, Astérisque No. 161-162, exp. no. 694, pp. 165-186.
        2. Masser, D. W. (1985). "Open problems". Proceedings of the Symposium on
           Analytic Number Theory. London: Imperial College.

    :param a: The first term of the potential triple. Must be a positive integer.
    :type a: int
    :param b: The second term of the potential triple. Must be a positive integer.
    :type b: int
    :return: The quality 'q' of the triple (a, b, a+b). Returns 0.0 if:
             - a or b is not positive.
             - a and b are not coprime (gcd(a,b) != 1).
             - a >= b (to ensure uniqueness and avoid redundant checks, as (a,b,c)
               and (b,a,c) are equivalent for quality calculation after ordering).
             - rad(abc) >= c (which implies q <= 1 or is undefined if rad=0 or 1).
             - rad(abc) = 0 or rad(abc) = 1 (denominator log(rad(abc)) would be undefined or zero).
    :rtype: float
    """
    if not (isinstance(a, int) and isinstance(b, int) and a > 0 and b > 0):
        return 0.0
    if (
        a >= b
    ):  # Ensure a < b for uniqueness, though quality is symmetric for a,b
        return 0.0
    if gcd(a, b) != 1:
        return 0.0

    c = a + b

    # Cache results of _radical to avoid re-computation for the same number
    @lru_cache(maxsize=1024)  # Adjust maxsize based on expected unique numbers
    def _radical(n_val: int) -> int:
        """
        Computes the radical (square-free kernel) of an integer 'n' using PARI/GP
        (via cypari2) for prime factorization. The radical of 'n' is the product
        of its distinct prime factors. This function is cached using
        `functools.lru_cache`.

        Example: rad(72) = rad(2^3 * 3^2) = 2 * 3 = 6.

        :param n_val: The integer for which to compute the radical.
        :type n_val: int
        :return: The radical of n_val. Returns 0 if n_val is 0, 1 if n_val is +/-1.
        :rtype: int
        :raises Exception: Propagates exceptions from PARI/GP factorization.
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
            if (
                len(distinct_primes) > 0
            ):  # Check if there are any prime factors
                for p in distinct_primes:
                    radical_val *= int(
                        p
                    )  # Convert PARI prime to int before multiplying
            # The 'else' case where distinct_primes is empty for abs(n_val) > 1
            # implies n_val is a prime power of a prime not handled by pari.factor (highly unlikely for standard integers)
            # or that n_val itself is prime and pari.factor returns it in a way not caught by len(distinct_primes)>0.
            # However, pari.factor([prime]) yields [[prime], [1]], so len(distinct_primes) would be 1.
            # This 'else' branch seems unreachable if pari.factor behaves as expected for integers > 1.
            # If abs(n_val) is 1, it's handled earlier. If abs(n_val) is prime, distinct_primes=[n_val].
            # Thus, this else block: `radical_val = abs(n_val) if abs(n_val) > 1 else 1` is likely dead code.
            # If it were reachable and len(distinct_primes) == 0 for abs(n_val) > 1, it would imply n_val has no prime factors,
            # which is impossible. The initial radical_val = 1 covers the case of n_val = 1 (after abs).
            # For safety or if PARI has some edge case returning empty factors for non-1 values, this could remain,
            # but it's confusing. Assuming standard integer factorization, it's not needed.
            # Removing the `else` part as it's covered by initialization `radical_val = 1` and loop, or prior checks.

            return radical_val
        except Exception as e:
            # Handle potential errors from PARI/GP, though it's robust.
            # This might occur for extremely large numbers beyond PARI's limits or config.
            logger.exception(
                f"Error during PARI/GP factorization of {n_val}: {e}"
            )
            # As a fallback, could use a simple Python version, but it would be slow.
            # For now, let it propagate. Could define a custom exception like PARIFactorizationError.
            raise  # Re-raise the exception to be handled by the caller.

    rad_abc = _radical(a * b * c)

    # If rad_abc is 0, it implies a,b,or c was 0.
    # If a or b were 0, it's caught by (a > 0 and b > 0) check.
    # c = a+b cannot be 0 if a,b > 0.
    # So rad_abc == 0 should not be hit here.
    # The main condition is rad_abc >= c (quality <= 1) or log(rad_abc) is undefined/problematic.
    if (
        rad_abc == 0
    ):  # Should ideally not be hit if initial checks on a,b are done.
        return 0.0

    # If rad_abc is 1 (meaning a*b*c was 1 or -1), and c > 1.
    # For positive integers a, b, if a*b*c = 1, then a=1, b=1, c=1. But c=a+b, so c=2. Contradiction.
    # So, a*b*c cannot be 1 if c > 1.
    # This means rad_abc cannot be 1 if c > 1 under the problem's constraints (a,b > 0, c=a+b).
    # The check `if rad_abc == 1 and c > 1:` is likely redundant given the constraints on a,b,c.
    # It's kept as a strong safeguard against log(1) in denominator.
    # If rad_abc is 1, math.log(rad_abc) is 0, leading to DivisionByZero.
    if rad_abc == 1:  # This implies log(rad_abc) would be 0.
        return 0.0  # Quality is undefined or infinite, return 0.0 as per problem spec for non-interesting triples.

    if (
        rad_abc >= c
    ):  # This ensures quality <=1, or if rad_abc is large, log(c)/log(rad_abc) is small.
        # It also implicitly handles cases where c=1 (log(c)=0).
        return 0.0

    try:
        # At this point, rad_abc > 1 and rad_abc < c.
        quality = math.log(c) / math.log(rad_abc)
    except ValueError:  # Should be caught by rad_abc >= c or rad_abc == 0
        return 0.0

    return quality
