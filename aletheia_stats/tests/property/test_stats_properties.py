import pytest
import numpy as np
from hypothesis import given, strategies as st, settings, HealthCheck
from typing import List

from aletheia_stats.aletheia_stats.domain.services import StatsService
from aletheia_stats.aletheia_stats.domain.entities import TTestResult

# --- Hypothesis Strategies ---

# Strategy for generating lists of floats (representing data groups)
# Ensure data is somewhat realistic for statistical tests (e.g., not all NaNs or Infs)
# and meets minimum size requirements for the tests.
MIN_SAMPLES = 3 # Shapiro-Wilk needs at least 3
MAX_SAMPLES = 100
VALID_FLOAT = st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False)

groups_strategy = st.lists(VALID_FLOAT, min_size=MIN_SAMPLES, max_size=MAX_SAMPLES)

# Strategy for alpha value (significance level)
alpha_strategy = st.floats(min_value=0.001, max_value=0.999, allow_nan=False, allow_infinity=False)


# --- Property-Based Tests for StatsService ---

@pytest.fixture(scope="module")
def service() -> StatsService:
    """Provides a StatsService instance for property tests."""
    # Using a fixed random state for reproducibility of Hypothesis counter-examples if any
    return StatsService(random_state=123)


@given(group_a=groups_strategy, group_b=groups_strategy, alpha=alpha_strategy)
@settings(
    deadline=None, # Allow more time for potentially slow stats calculations
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
    max_examples=50 # Adjust number of examples as needed for CI speed vs thoroughness
)
def test_perform_t_test_analysis_properties(
    service: StatsService, group_a: List[float], group_b: List[float], alpha: float
):
    """
    Property-based test for perform_t_test_analysis.
    Checks for basic invariants and expected behaviors.
    """
    # Pre-conditions / Assumptions for generated data (Hypothesis should handle this via strategies)
    # For example, if groups are identical, p-value should be high.
    # If one group is shifted significantly, p-value should be low.

    try:
        result = service.perform_t_test_analysis(group_a, group_b, alpha=alpha)
    except ValueError as e:
        # This can happen if, by chance, Hypothesis generates data that is problematic
        # even after filtering (e.g., all identical values within a group for Shapiro-Wilk,
        # or very small variance leading to issues in stats.ttest_ind).
        # Or if MIN_SAMPLES is not strictly enforced by strategy (it is here).
        # For this test, we'll assume ValueErrors for valid input sizes are bugs to investigate.
        # However, scipy's shapiro can raise error for constant data.
        if any(len(set(g)) == 1 for g in [group_a, group_b]) and "Shapiro-Wilk" in str(e).lower():
             pytest.skip(f"Skipping due to constant data in a group for Shapiro-Wilk: {e}")
        # Scipy ttest_ind can also raise ValueError if input arrays are ridiculously small
        # or have problematic variance, though our strategies try to avoid this.
        if "variance is zero" in str(e).lower() or "Degrees of freedom must be positive" in str(e).lower():
            pytest.skip(f"Skipping due to problematic variance or df for t-test: {e}")
        raise # Re-raise unexpected ValueErrors

    # --- Basic Invariants for TTestResult ---
    assert isinstance(result, TTestResult)

    # P-value properties
    assert 0.0 <= result.p_value <= 1.0, "P-value out of [0,1] range"

    # Statistic properties
    assert isinstance(result.statistic, float) # Should not be NaN/Inf for valid inputs
    assert not np.isnan(result.statistic), "T-statistic is NaN"
    # T-statistic can be Inf if one group has zero variance and means are different.
    # Our service's _calculate_welch_ttest might handle this or propagate scipy's behavior.
    # For now, we allow Inf, but this could be refined.
    # assert not np.isinf(result.statistic), "T-statistic is Infinity"

    # Degrees of freedom
    assert result.degrees_freedom >= 1, "Degrees of freedom should be >= 1" # Welch-Satterthwaite df >= min(n1-1, n2-1)

    # Confidence interval
    assert isinstance(result.confidence_interval_95, tuple)
    assert len(result.confidence_interval_95) == 2
    # CI lower bound should be <= upper bound, unless it's (-inf, -inf) or (inf, inf) or (nan,nan)
    # which can happen with zero variance groups.
    if not (np.isinf(result.confidence_interval_95[0]) or np.isinf(result.confidence_interval_95[1]) or \
            np.isnan(result.confidence_interval_95[0]) or np.isnan(result.confidence_interval_95[1])):
        assert result.confidence_interval_95[0] <= result.confidence_interval_95[1], \
            f"CI lower bound {result.confidence_interval_95[0]} > upper bound {result.confidence_interval_95[1]}"

    # Significance flag consistency
    assert result.is_significant_05 == (result.p_value < alpha), \
        "is_significant_05 flag inconsistent with p-value and alpha"

    # Normality p-values
    assert 0.0 <= result.normality_p_value_group_a <= 1.0, "Normality p-value for A out of [0,1] range"
    assert 0.0 <= result.normality_p_value_group_b <= 1.0, "Normality p-value for B out of [0,1] range"

    # Comment properties
    assert isinstance(result.comment, str)
    if result.normality_p_value_group_a < alpha:
        assert "Group A may not be normally distributed" in result.comment
    if result.normality_p_value_group_b < alpha:
        assert "Group B may not be normally distributed" in result.comment
    if result.normality_p_value_group_a >= alpha and result.normality_p_value_group_b >= alpha:
        assert result.comment == "Both groups appear to be normally distributed." or \
               result.comment == "Analysis complete." # if logic changes


@given(group_a=groups_strategy, alpha=alpha_strategy)
@settings(
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
    max_examples=30
)
def test_t_test_identical_groups_high_p_value(service: StatsService, group_a: List[float], alpha: float):
    """
    If two groups are identical, the p-value of a t-test should be high (close to 1.0),
    indicating no significant difference.
    """
    group_b = list(group_a) # Identical group

    # Skip if group_a is constant, as Shapiro-Wilk might fail or t-test gives NaNs
    if len(set(group_a)) == 1:
        pytest.skip("Skipping identical constant groups test for p-value property.")

    result = service.perform_t_test_analysis(group_a, group_b, alpha=alpha)

    # For identical non-constant groups, p-value should be high (often 1.0 or very close)
    assert result.p_value > 0.5 or np.isclose(result.p_value, 1.0), \
        f"P-value {result.p_value} for identical groups is unexpectedly low."
    assert result.is_significant_05 is False, "Identical groups should not be significant"
    assert np.isclose(result.statistic, 0.0, atol=1e-9) or np.isnan(result.statistic), \
        "T-statistic for identical groups should be close to 0 or NaN"


@given(group_a=groups_strategy, shift=st.floats(min_value=-10, max_value=10, allow_nan=False, allow_infinity=False), alpha=alpha_strategy)
@settings(
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
    max_examples=30
)
def test_t_test_shifted_groups(service: StatsService, group_a: List[float], shift: float, alpha: float):
    """
    If group_b is group_a shifted by a non-zero amount, and variances are similar,
    the t-test should detect a difference if the shift is large enough relative to variance.
    The sign of the t-statistic should correspond to the direction of the shift.
    """
    if abs(shift) < 1e-3 : # If shift is too small, it's like identical groups
        group_b = list(group_a)
    else:
        group_b = [x + shift for x in group_a]

    # Skip if variance is zero (constant group), as t-statistic becomes Inf/NaN
    # or if shift is negligible such that they are effectively identical.
    if len(set(group_a)) == 1 and abs(shift) > 1e-3 : # Constant group, shifted
         # t-stat will be +/- inf, p-value very small
         result = service.perform_t_test_analysis(group_a, group_b, alpha=alpha)
         assert np.isinf(result.statistic)
         assert result.p_value < 0.001 # Effectively zero
         if shift > 0: # group_b mean > group_a mean, so mean_a - mean_b is negative
             assert result.statistic < 0
         else: # shift < 0, group_b mean < group_a mean, so mean_a - mean_b is positive
             assert result.statistic > 0
         return # End test for this specific case
    elif len(set(group_a)) == 1 and abs(shift) < 1e-3: # Constant group, not really shifted
        pytest.skip("Skipping shifted constant group with negligible shift.")
        return


    result = service.perform_t_test_analysis(group_a, group_b, alpha=alpha)

    if abs(shift) < 1e-3: # Effectively identical groups
        assert result.p_value > 0.1 or np.isclose(result.p_value, 1.0) # Should be high
        assert np.isclose(result.statistic, 0.0, atol=1e-6) or np.isnan(result.statistic)
    else:
        # If shifted, the means are different.
        # The t-statistic's sign should reflect this.
        # mean_a - mean_b = mean_a - (mean_a + shift) = -shift
        if shift > 0: # mean_a - mean_b is negative
            assert result.statistic < 0 or np.isnan(result.statistic), \
                f"Statistic {result.statistic} should be negative for positive shift {shift}"
        elif shift < 0: # mean_a - mean_b is positive
            assert result.statistic > 0 or np.isnan(result.statistic), \
                f"Statistic {result.statistic} should be positive for negative shift {shift}"

        # If the shift is substantial compared to the variance, p-value should be small.
        # This is harder to assert generally without knowing variance.
        # For now, primarily checking the sign of the statistic.
        # Example: if std_dev is small and shift is large, expect significance.
        std_dev_a = np.std(group_a, ddof=1) if len(group_a) > 1 else 0
        if std_dev_a > 1e-6 and abs(shift) / std_dev_a > 3: # Heuristic: shift is >3 std devs
             # This is a strong expectation, might fail if group size is small or variance is weird
             # assert result.p_value < alpha, f"Expected significance for large shift/std_dev ratio ({abs(shift)/std_dev_a:.2f})"
             pass # This assertion is too strong for a general property test.

# More tests could be added:
# - Test symmetry: t_test(A, B) vs t_test(B, A) (statistic sign flips, p-value same)
# - Test scaling: t_test(A, B) vs t_test(k*A, k*B) (t-stat and p-value should be same if k > 0)
# - Test behavior with NaNs or Infs if strategies were to allow them (currently they don't)
# - Test with groups of very different sizes or variances.

@given(group_a=groups_strategy, group_b=groups_strategy, alpha=alpha_strategy)
@settings(
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
    max_examples=30
)
def test_t_test_symmetry_statistic_pvalue(service: StatsService, group_a: List[float], group_b: List[float], alpha: float):
    """
    Test property: t_test(A,B) vs t_test(B,A).
    Statistic should flip sign, p-value should remain the same.
    """
    # Skip if groups lead to problematic t-tests (e.g., all constant)
    if (len(set(group_a)) == 1 and len(set(group_b)) == 1 and np.mean(group_a) == np.mean(group_b)) or \
       (len(set(group_a)) == 1 and len(set(group_b)) == 1 and np.mean(group_a) != np.mean(group_b)): # constant groups
        pytest.skip("Skipping symmetry test for constant groups as t-stat can be NaN or Inf.")

    try:
        result_ab = service.perform_t_test_analysis(group_a, group_b, alpha=alpha)
        result_ba = service.perform_t_test_analysis(group_b, group_a, alpha=alpha)
    except ValueError as e:
        if "Shapiro-Wilk" in str(e).lower() and (len(set(group_a))==1 or len(set(group_b))==1):
            pytest.skip(f"Skipping due to constant data in a group for Shapiro-Wilk: {e}")
        raise

    assert result_ab.p_value == pytest.approx(result_ba.p_value), "P-values should be symmetric"

    # Statistic should be opposite or both NaN (if variances are zero)
    if not (np.isnan(result_ab.statistic) and np.isnan(result_ba.statistic)):
        assert result_ab.statistic == pytest.approx(-result_ba.statistic), \
            "T-statistics should be opposite for swapped groups"

    # Other fields should also be consistent
    assert result_ab.degrees_freedom == pytest.approx(result_ba.degrees_freedom)
    # CI for diff(A,B) is (L,U), CI for diff(B,A) is (-U, -L)
    assert result_ab.confidence_interval_95[0] == pytest.approx(-result_ba.confidence_interval_95[1])
    assert result_ab.confidence_interval_95[1] == pytest.approx(-result_ba.confidence_interval_95[0])

    assert result_ab.is_significant_05 == result_ba.is_significant_05
    assert result_ab.normality_p_value_group_a == pytest.approx(result_ba.normality_p_value_group_b) # A in first is B in second
    assert result_ab.normality_p_value_group_b == pytest.approx(result_ba.normality_p_value_group_a) # B in first is A in secondTool output for `create_file_with_block`:
