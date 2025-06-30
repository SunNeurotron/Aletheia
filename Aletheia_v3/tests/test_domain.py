# Aletheia_v3/tests/test_domain.py
import pytest
from Aletheia_v3.core.domain import get_quality, gcd, ABCTriple, ABCQuality

# --- Tests for gcd ---
@pytest.mark.parametrize("a, b, expected_gcd", [
    (10, 25, 5),
    (17, 23, 1), # Coprime
    (0, 5, 5),   # GCD with zero
    (5, 0, 5),
    (0, 0, 0),
    (12, 18, 6),
    (1, 1, 1),
    (7, 7, 7),
    (6, -9, 3), # With negative numbers (abs is taken)
    (-6, 9, 3),
    (-6, -9, 3),
])
def test_gcd(a, b, expected_gcd):
    """Tests the greatest common divisor function."""
    assert gcd(a, b) == expected_gcd

# --- Tests for get_quality ---

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
    quality = get_quality(a=3, b=125) # c = 128
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
    quality = get_quality(a=1, b=2400) # c = 2401
    assert quality == pytest.approx(1.45566, abs=1e-5)


@pytest.mark.parametrize("a, b, expected_q", [
    (1, 2, 0.0),          # gcd(1,2)=1, c=3, rad(1*2*3)=6. q = log3/log6 ~ 0.61. Not 0, but domain.get_quality might have threshold
                          # The domain.get_quality returns 0 if rad_abc >=c. Here rad(6) > c=3. So quality becomes 0.
    (2, 4, 0.0),          # Not coprime, gcd(2,4)=2
    (5, 5, 0.0),          # a >= b (a must be < b for current get_quality logic)
    (10, 3, 0.0),         # a >= b
    (-1, 5, 0.0),         # a is not positive
    (5, -1, 0.0),         # b is not positive
    (0, 5, 0.0),          # a is zero
    (1, 1, 0.0),          # a >= b (a must be < b for current get_quality logic)
                          # If we allowed a=1,b=1, c=2. rad(1*1*2)=2. q=log2/log2=1.
    (1, 0, 0.0)           # b is zero
])
def test_get_quality_invalid_inputs(a, b, expected_q):
    """Tests get_quality with various invalid or non-standard inputs."""
    assert get_quality(a, b) == expected_q

def test_get_quality_order_of_a_b():
    """
    The current domain.get_quality implementation expects a < b.
    If a > b, it returns 0.0.
    """
    assert get_quality(a=125, b=3) == 0.0 # a > b, should return 0 by current domain logic
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
    assert get_quality(a=1, b=6) == 0.0 # c=7
    # a=1, b=4, c=5 (prime)
    # rad(abc) = rad(1*4*5) = rad(2^2*5) = 2*5 = 10.
    # Since rad(10) > c(5), quality should be 0.0
    assert get_quality(a=1, b=4) == 0.0 # c=5

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
