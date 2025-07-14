# Copyright 2025 Alant
#
# Licensed under the Aletheia Unificada Ethical Public License (AUEPL);
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

# Aletheia_v3/tests/test_domain.py
from functools import lru_cache

import pytest

from Aletheia_v3.core.domain import ABCQuality, ABCTriple
# from Aletheia_v3.core.domain import _radical as domain_radical_func # _radical is a local function in get_quality
from Aletheia_v3.core.domain import gcd, get_quality, CYPARI2_AVAILABLE, pari as cypari_instance # pari is used internally in domain.py, also import CYPARI2_AVAILABLE and pari for tests

# --- Tests for gcd (now using PARI/GP if available, else math.gcd) ---
@pytest.mark.parametrize(
    "a, b, expected_gcd",
    [
        (10, 25, 5),
        (17, 23, 1),  # Coprime
        (0, 5, 5),
        (5, 0, 5),
        (0, 0, 0),
        (12, 18, 6),
        (1, 1, 1),
        (7, 7, 7),
        (6, -9, 3),  # With negative numbers
        (-6, 9, 3),
        (-6, -9, 3),
        (10**18, 25 * 10**9, int(25 * 10**9)),  # Python large integers
        (10**50, 25 * 10**30, int(25 * 10**30)), # Python very large integers
    ],
)
def test_gcd_behavior(a, b, expected_gcd):
    """Tests the gcd function which uses PARI/GP if available, else math.gcd."""
    assert gcd(a, b) == expected_gcd


# --- Tests for _radical (now using PARI/GP and cached) ---
# The _radical function is local to get_quality, so it's tested implicitly via get_quality.
# Direct tests for _radical and its caching fixture are removed.


# --- Tests for get_quality (now using PARI/GP backed gcd and _radical) ---


def test_get_quality_valid_known_hit():
    """
    Tests get_quality with a known high-quality hit.
    Example: a=1, b=8, c=9. rad(1*8*9) = rad(72) = rad(2^3 * 3^2) = 2*3 = 6.
    q = log(9)/log(6) approx 0.954 / 0.778 = 1.226...
    Let's use a more famous one: a=2, b=3^10*109 = 6436341, c = a+b = 6436343. rad(abc) = 2*3*109*rad(c)
    A known high quality hit: a=3, b=125 (5^3), c=128 (2^7)
    rad(abc) = rad(3 * 5^3 * 2^7) = rad(3 * 5 * 2) = 30
    q = log(128) / log(30) = log(2^7) / log(30) = 7*log(2) / log(30)
    q approx 7 * 0.30103 / 1.47712 = 2.10721 / 1.47712 approx 1.42657
    """
    quality = get_quality(a=3, b=125)  # c = 128
    assert quality == pytest.approx(1.42657, abs=1e-5)


def test_get_quality_another_valid_hit():
    """
    Another example: a=1, b=48 = 3 * 2^4, c=49 = 7^2
    rad(abc) = rad(1 * (3*2^4) * 7^2) = rad(3*2*7) = 42
    q = log(49) / log(42) = log(7^2) / log(42) = 2*log(7) / log(42)
    q approx 2 * 0.84509 / 1.62324 = 1.69018 / 1.62324 approx 1.04123
    This is a valid hit, but quality might not be > 1.4 threshold often used.
    Let's test a known hit that typically passes the 1.4 threshold.
    Example: a = 1, b = 2 * 3^k - 1 (for some k), c = 2*3^k
    Consider Szpiro's conjecture example: a=1, b=2400=2^5*3*5^2, c=2401=7^4
    rad(abc) = rad(2*3*5*7) = 210
    q = log(2401) / log(210) = log(7^4) / log(210) = 4*log(7)/log(210)
    q approx 4*0.845098 / 2.322219 = 3.380392 / 2.322219 approx 1.45566
    """
    quality = get_quality(a=1, b=2400)  # c = 2401
    assert quality == pytest.approx(1.45566, abs=1e-5)


@pytest.mark.parametrize(
    "a, b, expected_q",
    [
        (
            1,
            2,
            0.0,
        ),  # gcd(1,2)=1, c=3, rad(1*2*3)=6. q = log3/log6 ~ 0.61. Not 0, but domain.get_quality might have threshold
        # The domain.get_quality returns 0 if rad_abc >=c. Here rad(6) > c=3. So quality becomes 0.
        (2, 4, 0.0),  # Not coprime, gcd(2,4)=2
        (5, 5, 0.0),  # a >= b (a must be < b for current get_quality logic)
        (10, 3, 0.0),  # a >= b
        (-1, 5, 0.0),  # a is not positive
        (5, -1, 0.0),  # b is not positive
        (0, 5, 0.0),  # a is zero
        (1, 1, 0.0),  # a >= b (a must be < b for current get_quality logic)
        # If we allowed a=1,b=1, c=2. rad(1*1*2)=2. q=log2/log2=1.
        (1, 0, 0.0),  # b is zero
    ],
)
def test_get_quality_invalid_inputs(a, b, expected_q):
    """Tests get_quality with various invalid or non-standard inputs."""
    assert get_quality(a, b) == expected_q


def test_get_quality_order_of_a_b():
    """
    The current domain.get_quality implementation expects a < b.
    If a > b, it returns 0.0.
    """
    assert (
        get_quality(a=125, b=3) == 0.0
    )  # a > b, should return 0 by current domain logic
    # Symmetric quality if inputs were ordered:
    # quality_ordered = get_quality(a=3, b=125)
    # assert quality_ordered > 1.4 # This is tested in test_get_quality_valid_known_hit


def test_abctriple_creation():
    """Tests creation of ABCTriple dataclass."""
    triple = ABCTriple(a=1, b=2, c=3)
    assert triple.a == 1
    assert triple.b == 2
    assert triple.c == 3


def test_abcquality_creation():
    """Tests creation of ABCQuality dataclass."""
    triple = ABCTriple(a=1, b=2, c=3)
    abc_q = ABCQuality(triple=triple, quality=1.23)
    assert abc_q.triple == triple
    assert abc_q.quality == 1.23


# Test with a case where rad_abc == c, which should result in quality 0
# e.g. a=1, b=2, c=3. rad(abc)=6. log(3)/log(6) = 0.613. But domain.get_quality returns 0 because rad_abc > c.
# e.g. a=1, b=p-1, c=p where p is prime. rad(abc) = rad( (p-1) * p ).
# If a=1, b=1, c=2 (a=1, b=1 not allowed by a<b).
# If a=1, b=7, c=8. rad(1*7*8) = rad(7*2^3) = 14. log(8)/log(14) ~ 0.78. rad_abc > c, so 0.
def test_get_quality_rad_greater_than_c():
    # a=1, b=7, c=8. rad(abc) = rad(1*7*8) = rad(56) = rad(2^3 * 7) = 2*7 = 14.
    # Since rad(14) > c(8), quality should be 0.0 as per domain logic.
    assert get_quality(a=1, b=7) == 0.0


# Test with a case where c is prime, a=1, b=c-1
# a=1, b=6, c=7 (prime)
# rad(abc) = rad(1*6*7) = rad(2*3*7) = 42.
# Since rad(42) > c(7), quality should be 0.0.
def test_get_quality_c_is_prime():
    assert get_quality(a=1, b=6) == 0.0  # c=7
    # a=1, b=4, c=5 (prime)
    # rad(abc) = rad(1*4*5) = rad(2^2*5) = 2*5 = 10.
    # Since rad(10) > c(5), quality should be 0.0
    assert get_quality(a=1, b=4) == 0.0  # c=5


# Test a specific case from literature if possible
# E.g., Frey's curve relation: if x^p + y^p = z^p, then A=x^p, B=y^p, C=z^p
# This is more about the conjecture itself than the quality function for arbitrary a,b.

# The domain.py's get_quality has specific conditions for returning 0.0:
# - not (isinstance(a, int) and isinstance(b, int) and a > 0 and b > 0)
# - a >= b
# - gcd(a, b) != 1
# - rad_abc == 0 or rad_abc >= c
# - rad_abc == 1 and c > 1 (This is a specific edge case for log(1)=0)


def test_get_quality_rad_is_one_c_greater_than_one():
    """
    Test the condition where rad_abc == 1 and c > 1.
    This can only happen if a*b*c is 1 or -1.
    Given a,b > 0, a*b*c > 0. So a*b*c must be 1.
    This implies a=1, b=1, c=1 (but c=a+b, so this isn't possible).
    Or a=1, b=1, c=2. rad(1*1*2) = 2. Not 1.
    This condition `rad_abc == 1 and c > 1` in domain.py seems hard to hit
    with positive a,b and c=a+b, because if rad_abc=1, then abc=1.
    If a,b are positive integers, a=1, b=1 => c=2. abc=2. rad(2)=2.
    If a=1, (no b possible for abc=1 and b>0).
    The only way rad_abc = 1 is if a=1, b=1, c=1, but c must be a+b.
    So this specific check in domain.py might be for a more general _radical function
    if it were used elsewhere, or a safeguard that's effectively not hit for abc-triples.
    Let's assume the other conditions correctly cover practical cases for abc-triples.
    """
    # This case should not be possible for valid a, b (positive integers, a < b, c = a+b)
    # because if rad_abc = 1, then a*b*c has no prime factors, meaning a*b*c = 1.
    # If a=1, b must be < 1 or 0 to make b*c = 1 (since a=1). This violates b > 0.
    # So, this specific path in get_quality is unlikely to be triggered by valid (a,b) inputs.
    pass


# Test for floating point precision issues if any are suspected, though unlikely with math.log
# pytest.approx is good for this.

# Consider testing the _radical function directly if it were not private,
# but since it's part of get_quality's implementation, testing get_quality covers it.
# Example: _radical(72) = _radical(2^3 * 3^2) = 2*3 = 6.
# Example: _radical(1) = 1
# Example: _radical(0) = 0 (as per domain.py)
# Example: _radical(7) = 7 (prime)
# Example: _radical(6) = 2*3 = 6
# Example: _radical(prod of distinct primes) = prod of distinct primes.
# These are implicitly tested via get_quality.


# Final check on a simple, low-quality valid triple
# a=1, b=2, c=3. gcd(1,2)=1. rad(1*2*3)=6.
# log(3)/log(6) = 0.4771 / 0.7781 ~ 0.6131
# domain.py returns 0 because rad(6) > c(3).
def test_get_quality_simple_low_quality_valid_triple():
    assert get_quality(a=1, b=2) == 0.0


# a=2, b=3, c=5. gcd(2,3)=1. rad(2*3*5)=30.
# log(5)/log(30) = 0.6989 / 1.4771 ~ 0.4731
# domain.py returns 0 because rad(30) > c(5).
def test_get_quality_another_simple_low_quality_valid_triple():
    assert get_quality(a=2, b=3) == 0.0


def test_get_quality_with_large_numbers():
    """
    Tests get_quality with larger numbers, relying on PARI/GP's capabilities.
    Example: a = 2^k - 1, b = 1, c = 2^k (Beal's conjecture counter-example form if gcd(a,b,c)>1)
    Let's choose a known high-quality triple with larger components if available,
    or construct one where calculations are feasible to verify.

    Consider a hypothetical large triple (simplified for testing PARI integration):
    a = 3
    b_large = 5**30 # A large number
    # c_large = 3 + 5**30
    # rad_abc = rad(3 * 5**30 * (3+5**30)) = rad(3 * 5 * (3+5**30))
    # This requires factoring 3+5**30, which PARI can do.
    # For test predictability, let's use numbers where rad(abc) is simpler.

    # Let a = small prime, b = power of another small prime, c = a+b
    # Example: a=7, b=2**40 (large). c = 7 + 2**40
    # rad(abc) = rad(7 * 2**40 * (7+2**40)) = rad(7 * 2 * (7+2**40))
    # This still needs factoring 7+2**40.

    # Let's use a case similar to known high-quality hits but scaled up,
    # ensuring a,b are coprime and a < b.
    # Based on 3 + 125 = 128 -> q ~ 1.42657
    # a = 3
    # b = 5^k. Let k=20. b = 5^20
    # c = 3 + 5^20
    # rad(abc) = rad(3 * 5^20 * (3+5^20)) = rad(3 * 5 * (3+5^20))

    # For a predictable test, let a=1, b such that a,b coprime and c=a+b is a power of a prime.
    # Example: a=1, b = 2*3^10 - 1 = 118097. c = 2*3^10 = 118098.
    # gcd(1, 118097) = 1.
    # rad(abc) = rad(1 * 118097 * 118098)
    # 118097 is prime.
    # 118098 = 2 * 3^10 * 1. So rad(118098) = 2*3 = 6.
    # rad(abc) = rad(118097 * 2 * 3) = 2 * 3 * 118097 = 708582
    # q = log(c) / log(rad(abc)) = log(118098) / log(708582)
    # q = log(118098) / log(708582) approx 5.0722 / 5.8503 approx 0.8669
    # This is a valid triple, but low quality.

    a_large = 1
    b_large = 118097 # prime
    # c_large = 1 + 118097 = 118098
    # This specific case has quality < 1 so it might return 0 if rad_abc >= c
    # log(118098) / log(rad(1*118097*118098)) = log(118098) / log(2*3*118097)
    # = 11.679 / 13.470 = 0.8669...
    # Since rad = 708582 > c = 118098, get_quality will return 0.0.
    assert get_quality(a=a_large, b=b_large) == 0.0

    # Test with a known very high quality hit, e.g. Szpiro's original example
    # a=1, b= (2^n * k) - 1, c = 2^n * k
    # The "ABC Triple of the year 2000": 2, 3^10 * 109, 2 + 3^10 * 109
    # a = 2
    # b = 3**10 * 109 = 59049 * 109 = 6436341
    # c = a + b = 6436343 (which is prime)
    # rad(abc) = rad(2 * (3**10 * 109) * 6436343)
    #          = rad(2 * 3 * 109 * 6436343)
    #          = 2 * 3 * 109 * 6436343 (since 2,3,109, and c are prime and distinct)
    #          = 654 * 6436343 = 4273368132
    # q = log(c) / log(rad(abc)) = log(6436343) / log(4273368132)
    #   = 6.80863 / 9.63076 approx 0.70696. This is wrong.
    # The actual known quality for (2, 6436341, 6436343) is q=1.6299...
    # Let's re-check rad calculation for this famous triple.
    # a=2, b=3^10 * 109, c=a+b = 6436343 (prime)
    # rad(a) = 2
    # rad(b) = rad(3^10 * 109) = 3 * 109 = 327
    # rad(c) = 6436343 (since c is prime)
    # rad(abc) = rad(a)*rad(b)*rad(c) because a,b,c are coprime.
    # gcd(a,b) = gcd(2, 3^10*109) = 1.
    # gcd(a,c) = gcd(2, 6436343) = 1 (c is odd).
    # gcd(b,c) = gcd(3^10*109, 2+3^10*109). If p divides b and c, then p divides c-b=2. So p=2. But b is odd. So gcd(b,c)=1.
    # Thus a,b,c are pairwise coprime.
    # rad(abc) = rad(a) * rad(b) * rad(c) = 2 * (3*109) * 6436343 = 2 * 327 * 6436343 = 654 * 6436343 = 4209368122
    # q = log(6436343) / log(4209368122)
    # log10(6436343) ~ 6.8086
    # log10(4209368122) ~ 9.6242
    # q ~ 6.8086 / 9.6242 ~ 0.7074 -- this is still not matching 1.6299.
    # The definition of rad(abc) is product of distinct primes dividing abc.
    # Primes dividing a: {2}
    # Primes dividing b: {3, 109}
    # Primes dividing c: {6436343} (since c is prime)
    # Distinct primes dividing a*b*c are {2, 3, 109, 6436343}.
    # So rad(abc) = 2 * 3 * 109 * 6436343 = 4209368122.
    # The formula is correct. Why is the known q different?
    # Ah, the famous Reyssal triple is (a=2, b=3^10*109 = 6436341, c=a+b=6436343)
    # Its quality is q(a,b,c) = log(c) / log(rad(a*b*c)).
    # Let's use the values from a reliable source for rad(abc) for this triple.
    # For (2, 3^10*109, 6436343), rad(abc) = 2*3*109*6436343. This seems correct.
    # Perhaps the definition of quality I am using or the value of c is slightly off from the source of q=1.6299
    # Or my log values. Using math.log (natural log):
    # math.log(6436343) approx 15.6775
    # math.log(4209368122) approx 22.1608
    # q approx 15.6775 / 22.1608 = 0.7074...
    # This implies that the provided example (2, 3^10*109, ...) is NOT the one with q=1.6299,
    # or my understanding of its rad(abc) is flawed.
    # The triple with q ~ 1.6299 is A. Nitaj's triple:
    # a = 13^4 = 28561
    # b = 2^15 * 3 * 5^2 * 7^2 * 11 = 32768 * 3 * 25 * 49 * 11 = 1323206400
    # c = a+b = 1323234961 (prime)
    # rad(abc) = rad(13 * 2*3*5*7*11 * c) = 13*2*3*5*7*11 * 1323234961 = 30030 * 1323234961
    # This is too complex for a quick test addition.

    # Let's stick to the ones already tested (like a=1, b=2400, q ~ 1.45566)
    # and ensure they work with the PARI backend. The existing tests cover this.
    # The purpose here is more about testing large number handling by PARI through get_quality.
    # We can use a synthetic large number case that's easier to calculate rad for.
    a_syn = 7
    # b_syn needs to be large, and gcd(a_syn, b_syn) = 1
    # Let b_syn = 11**30 (11 to a large power, 11 is not 7)
    b_syn = 11**30
    # c_syn = 7 + 11**30
    # rad(a_syn * b_syn * c_syn) = rad(7 * 11**30 * (7+11**30))
    # rad = 7 * 11 * rad(7+11**30)
    # This still requires factoring 7+11**30.
    # PARI should handle this. We expect a float result.
    # If 7+11**30 is prime, rad = 7 * 11 * (7+11**30)
    # q = log(7+11**30) / log(7*11*(7+11**30)). This will be < 1.
    # So, get_quality should return 0.0 if rad_abc >= c.

    # If rad(7+11**30) is small, q could be > 1.
    # Example: if 7+11**30 = K^m where K is small.
    # This is essentially what the conjecture is about.

    # We expect get_quality to run without error for large numbers.
    # The actual value might be 0.0 if quality < 1 or other conditions met.
    try:
        q_large = get_quality(a=a_syn, b=int(b_syn)) # b_syn might be a PARI int if not careful
        assert isinstance(q_large, float) # Should return a float
        # We don't have an easy expected value here without deep math,
        # but we check it runs and returns a float (likely 0.0 for random large choices).
    except Exception as e:
        pytest.fail(f"get_quality failed with large numbers a={a_syn}, b={b_syn}: {e}")

    # Test a case that should give a non-zero quality, but with large numbers
    # (a=1, b=2^60-1, c=2^60). Assume b is prime for simplicity of rad calculation.
    # If b = 2^60-1 is prime (Mersenne prime M61 is 2^61-1, M59 is not prime).
    # (2^60-1) is divisible by 3, 5, 11, ... so not prime.
    # This shows that constructing good large number tests for get_quality is non-trivial.
    # The existing tests for known high-quality hits are the most reliable.
    # The main new aspect is that PARI handles the intermediate large number arithmetic.
    pass # Rely on existing high-quality hit tests for correctness with PARI.
    """
