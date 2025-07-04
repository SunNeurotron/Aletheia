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

# Aletheia_v3/tests/test_custom_acquisitions.py
import math

import pytest

from Aletheia_v3.core.custom_acquisitions import (
    PRIME_POWER_SERIES_CACHE,
    SMALL_PRIMES_FOR_HEURISTIC,
    _get_prime_power_series,
    get_structural_bonus,
)


@pytest.fixture(autouse=True)
def clear_caches():
    PRIME_POWER_SERIES_CACHE.clear()


class TestGetPrimePowerSeries:
    def test_empty_for_invalid_inputs(self):
        assert _get_prime_power_series(1, 100) == []
        assert (
            _get_prime_power_series(2, 1) == []
        )  # prime > value_upper_bound essentially
        assert _get_prime_power_series(7, 5) == []

    def test_correct_series_generated(self):
        assert _get_prime_power_series(2, 32) == [2, 4, 8, 16, 32]
        assert _get_prime_power_series(3, 81) == [3, 9, 27, 81]
        assert _get_prime_power_series(5, 100) == [
            5,
            25,
        ]  # 125 is > 100 * 1.5 (default margin)
        assert _get_prime_power_series(5, 125) == [5, 25, 125]

    def test_upper_bound_respected(self):
        series = _get_prime_power_series(
            2, 30
        )  # Max power should be 16 (32 is > 30*1.5=45 is false, 32 < 45)
        # 2^4=16. 2^5=32. 30*1.5 = 45. So 32 should be included.
        assert 32 in series
        assert 64 not in series  # if MAX_POWER_FOR_HEURISTIC is high enough

    def test_cache_usage(self):
        PRIME_POWER_SERIES_CACHE.clear()
        _get_prime_power_series(2, 100)
        assert (
            2,
            8,
        ) in PRIME_POWER_SERIES_CACHE  # log2(100) approx 6.64 -> effective_max_exponent = min(40, 6+2=8)
        initial_cache_size = len(PRIME_POWER_SERIES_CACHE)

        _get_prime_power_series(2, 100)  # Call again
        assert (
            len(PRIME_POWER_SERIES_CACHE) == initial_cache_size
        )  # Should hit cache

        _get_prime_power_series(3, 100)  # New prime
        assert len(PRIME_POWER_SERIES_CACHE) > initial_cache_size


class TestGetStructuralBonus:
    @pytest.mark.parametrize(
        "value, expected_base_bonus_factor",
        [
            (2, 1.0),
            (3, 1.0),
            (4, 1.0),
            (5, 1.0),
            (7, 1.0),
            (8, 1.0),
            (9, 1.0),
            (11, 1.0),
            (13, 1.0),
            (16, 1.0),
            (25, 1.0),
            (27, 1.0),
            (32, 1.0),
        ],
    )
    def test_exact_prime_power_max_bonus(
        self, value, expected_base_bonus_factor
    ):
        # Test with default scale_factor=0.05, exact_match_multiplier=2.0
        # Expected bonus = 0.05 * 2.0 = 0.1
        if value not in SMALL_PRIMES_FOR_HEURISTIC and not any(
            value == p**i
            for p in SMALL_PRIMES_FOR_HEURISTIC
            for i in range(2, 7)
        ):
            # This check is a bit tautological for the test itself, but ensures test values are meaningful
            pass  # these are prime powers of the small primes

        assert get_structural_bonus(
            value, bonus_scale_factor=0.05, exact_match_multiplier=2.0
        ) == pytest.approx(0.05 * 2.0 * expected_base_bonus_factor)

    def test_value_is_small_prime_itself(self):
        assert (
            get_structural_bonus(
                17, bonus_scale_factor=0.05, exact_match_multiplier=2.0
            )
            == 0.0
        )
        # 17 is not in SMALL_PRIMES_FOR_HEURISTIC by default [2,3,5,7,11,13]
        # If it were, it would be 0.05 * 2.0. Let's test one that is.
        assert get_structural_bonus(
            7, bonus_scale_factor=0.05, exact_match_multiplier=2.0
        ) == pytest.approx(0.05 * 2.0)

    @pytest.mark.parametrize(
        "value, proximity_to_power, expected_decay_factor_approx",
        [
            (
                31,
                "near_32_2^5",
                math.exp(-5.0 * abs(31 - 32) / 32),
            ),  # Proximity to 32 (2^5)
            (30, "near_32_2^5", math.exp(-5.0 * abs(30 - 32) / 32)),
            (26, "near_27_3^3", math.exp(-5.0 * abs(26 - 27) / 27)),
            (
                100,
                "near_81_3^4_or_121_11^2_or_125_5^3",
                min(
                    math.exp(-5.0 * abs(100 - 81) / 81),
                    math.exp(-5.0 * abs(100 - 121) / 121),
                    math.exp(-5.0 * abs(100 - 125) / 125),
                ),
            ),
        ],
    )
    def test_proximity_bonus_decay(
        self, value, proximity_to_power, expected_decay_factor_approx
    ):
        # Test with default scale_factor=0.05, proximity_penalty_factor=5.0
        # Expected bonus = 0.05 * decay_factor
        expected_bonus = 0.05 * expected_decay_factor_approx
        # If bonus is less than 1% of scale_factor (0.0005), it becomes 0.0
        if expected_bonus < (0.05 * 0.01):
            expected_bonus = 0.0
        assert get_structural_bonus(
            value, bonus_scale_factor=0.05, proximity_penalty_factor=5.0
        ) == pytest.approx(expected_bonus, abs=1e-4)

    def test_no_bonus_for_far_numbers(self):
        # A number that is not a prime power and not particularly close to one
        # e.g. a large prime not in SMALL_PRIMES_FOR_HEURISTIC
        large_prime = 101
        assert (
            get_structural_bonus(large_prime) == 0.0
        )  # Should be far from powers of 2,3,5,7,11,13

    def test_invalid_inputs(self):
        assert get_structural_bonus(1) == 0.0
        assert get_structural_bonus(0) == 0.0
        assert get_structural_bonus(-10) == 0.0
        assert get_structural_bonus("abc") == 0.0  # type: ignore

    def test_bonus_scale_factor_respected(self):
        assert get_structural_bonus(
            32, bonus_scale_factor=0.1, exact_match_multiplier=2.0
        ) == pytest.approx(0.1 * 2.0)
        bonus_near = get_structural_bonus(
            31, bonus_scale_factor=0.1, proximity_penalty_factor=5.0
        )
        expected_decay = math.exp(-5.0 * abs(31 - 32) / 32)
        assert bonus_near == pytest.approx(0.1 * expected_decay)

    def test_very_large_number_prime_power(self):
        val = 2**35  # Is a power of a small prime
        assert get_structural_bonus(
            val, bonus_scale_factor=0.05, exact_match_multiplier=2.0
        ) == pytest.approx(0.1)

    def test_very_large_number_near_prime_power(self):
        val = 2**35 - 1
        expected_decay = math.exp(-5.0 * abs(val - 2**35) / (2**35))
        expected_bonus = 0.05 * expected_decay
        if expected_bonus < (0.05 * 0.01):
            expected_bonus = 0.0
        assert get_structural_bonus(
            val, bonus_scale_factor=0.05, proximity_penalty_factor=5.0
        ) == pytest.approx(expected_bonus)
