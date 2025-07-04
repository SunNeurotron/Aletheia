from typing import List, Tuple

import numpy as np
import scipy.stats as stats

from .entities import TTestResult


class StatsService:
    """
    Provides statistical calculation services.

    This service encapsulates the logic for performing statistical tests,
    ensuring that the methods are well-documented and adhere to scientific rigor.
    """

    def __init__(self, random_state: int = 42):
        """
        Initializes the StatsService.

        Args:
            random_state: Seed for any stochastic processes to ensure reproducibility.
                          Currently not used by t-test or Shapiro-Wilk directly,
                          but good practice for future extensions.
        """
        self.random_state = random_state
        np.random.seed(
            self.random_state
        )  # For reproducibility if any numpy RNG is used

    def _calculate_welch_ttest(
        self,
        group_a: List[float],
        group_b: List[float],
        alpha: float = 0.05,
    ) -> Tuple[float, float, float, Tuple[float, float]]:
        """
        Performs Welch's t-test for two independent samples.
        Assumes unequal variances.

        Args:
            group_a: List of numerical data for group A.
            group_b: List of numerical data for group B.
            alpha: Significance level for the confidence interval.

        Returns:
            A tuple containing:
            - t_statistic (float)
            - p_value (float)
            - degrees_freedom (float)
            - confidence_interval (Tuple[float, float]) for the difference in means.

        @equations:
            The t-statistic is calculated as:
            \\[ t = \\frac{\\bar{x}_1 - \\bar{x}_2}{\\sqrt{\\frac{s_1^2}{n_1} + \\frac{s_2^2}{n_2}}} \\]
            Degrees of freedom (Welch-Satterthwaite equation):
            \\[ \\text{df} \\approx \\frac{(\\frac{s_1^2}{n_1} + \\frac{s_2^2}{n_2})^2}{\\frac{(s_1^2/n_1)^2}{n_1-1} + \\frac{(s_2^2/n_2)^2}{n_2-1}} \\]

        @references:
            - Welch, B. L. (1947). "The generalization of "Student's" problem when
              several different population variances are involved". Biometrika. 34 (1–2): 28–35.
            - SciPy documentation: `scipy.stats.ttest_ind`
        """
        if len(group_a) < 2 or len(group_b) < 2:
            raise ValueError(
                "Each group must contain at least two observations for t-test."
            )

        # Perform Welch's t-test (assumes unequal variances)
        t_statistic, p_value = stats.ttest_ind(
            group_a, group_b, equal_var=False, nan_policy="raise"
        )

        # Calculate degrees of freedom using Welch-Satterthwaite equation
        # scipy.stats.ttest_ind with equal_var=False already uses Welch's t-test,
        # but it doesn't directly return the df. We can approximate it or use statsmodels for exact df.
        # For simplicity, we'll use an approximation or rely on scipy's internal handling for p-value.
        # A common way to get df for Welch's t-test if not provided by the ttest_ind function:
        n1, n2 = len(group_a), len(group_b)
        s1_sq, s2_sq = np.var(group_a, ddof=1), np.var(group_b, ddof=1)

        if s1_sq == 0 and s2_sq == 0:  # Both groups have zero variance
            degrees_freedom = float(
                n1 + n2 - 2
            )  # Or handle as a special case / error
        elif s1_sq == 0 or s2_sq == 0:  # One group has zero variance
            # This case can be problematic for Welch-Satterthwaite.
            # Scipy handles it internally for p-value. For CI, this might need specific handling.
            # Let's use a large number for df, or one less than the non-zero variance group size.
            degrees_freedom = float(n1 - 1 if s2_sq == 0 else n2 - 1)
            if n1 < 2 or n2 < 2:
                degrees_freedom = 1.0  # avoid df < 1

        else:
            df_num = (s1_sq / n1 + s2_sq / n2) ** 2
            df_den = ((s1_sq / n1) ** 2 / (n1 - 1)) + (
                (s2_sq / n2) ** 2 / (n2 - 1)
            )
            degrees_freedom = df_num / df_den

        if degrees_freedom < 1:  # Ensure df is at least 1 for t.interval
            degrees_freedom = 1.0

        # Calculate confidence interval for the difference in means
        diff_mean = np.mean(group_a) - np.mean(group_b)
        std_err_diff = np.sqrt(s1_sq / n1 + s2_sq / n2)

        if (
            std_err_diff == 0
        ):  # Avoid division by zero if both groups are constant and identical
            confidence_interval = (diff_mean, diff_mean)
        else:
            confidence_interval = stats.t.interval(
                1 - alpha,
                df=degrees_freedom,
                loc=diff_mean,
                scale=std_err_diff,
            )
        return t_statistic, p_value, degrees_freedom, confidence_interval

    def perform_t_test_analysis(
        self, group_a: List[float], group_b: List[float], alpha: float = 0.05
    ) -> TTestResult:
        """
        Performs an independent two-sample t-test analysis, including normality checks.

        Args:
            group_a: List of numerical data for group A.
            group_b: List of numerical data for group B.
            alpha: Significance level for determining significance and for CI.

        Returns:
            A TTestResult object containing all analysis details.

        Raises:
            ValueError: If input data is insufficient (e.g., less than 3 samples
                        for Shapiro-Wilk, or less than 2 for t-test).
        """
        if len(group_a) < 3 or len(group_b) < 3:
            # Shapiro-Wilk test requires at least 3 samples.
            # Welch's t-test requires at least 2 samples per group.
            # We enforce 3 for normality check, which is a common pre-requisite.
            raise ValueError(
                "Each group must contain at least three observations for normality testing and t-test."
            )

        # 1. Normality Check (Shapiro-Wilk test)
        # @equation: Shapiro-Wilk W statistic (complex formula, not shown here)
        # @reference: Shapiro, S. S., & Wilk, M. B. (1965). "An analysis of variance test for
        #             normality (complete samples)". Biometrika. 52 (3–4): 591–611.
        normality_stat_a, normality_p_a = stats.shapiro(group_a)
        normality_stat_b, normality_p_b = stats.shapiro(group_b)

        comment = ""
        if normality_p_a < alpha:
            comment += f"Group A may not be normally distributed (Shapiro-Wilk p={normality_p_a:.3f}). "
        if normality_p_b < alpha:
            comment += f"Group B may not be normally distributed (Shapiro-Wilk p={normality_p_b:.3f}). "

        if not comment:
            comment = "Both groups appear to be normally distributed."

        # 2. Perform Welch's T-Test (assuming unequal variances by default)
        t_statistic, p_value, df, ci = self._calculate_welch_ttest(
            group_a, group_b, alpha
        )

        # 3. Compile results
        is_significant = p_value < alpha
        mean_a = np.mean(group_a)
        mean_b = np.mean(group_b)
        var_a = np.var(group_a, ddof=1)
        var_b = np.var(group_b, ddof=1)

        return TTestResult(
            statistic=float(t_statistic),
            p_value=float(p_value),
            degrees_freedom=float(df),
            confidence_interval_95=ci,
            mean_group_a=float(mean_a),
            mean_group_b=float(mean_b),
            variance_group_a=float(var_a),
            variance_group_b=float(var_b),
            is_significant_05=is_significant,
            normality_p_value_group_a=float(normality_p_a),
            normality_p_value_group_b=float(normality_p_b),
            comment=comment.strip() if comment else "Analysis complete.",
        )


# Example Usage (optional)
if __name__ == "__main__":
    service = StatsService()

    # Example Data
    group1_normal = [2.1, 2.5, 2.7, 3.0, 3.1, 3.5, 3.6, 4.0, 4.1, 4.5]  # n=10
    group2_normal = [
        3.0,
        3.2,
        3.5,
        3.8,
        4.0,
        4.2,
        4.5,
        4.8,
        5.0,
        5.5,
    ]  # n=10, different mean

    group3_non_normal = [1, 1, 1, 10, 10, 10]  # n=6
    group4_small = [1, 2]  # n=2

    print("--- Test Case 1: Normal data, different means ---")
    try:
        result1 = service.perform_t_test_analysis(group1_normal, group2_normal)
        print(f"T-Statistic: {result1.statistic:.3f}")
        print(f"P-Value: {result1.p_value:.3f}")
        print(f"Degrees of Freedom: {result1.degrees_freedom:.2f}")
        print(
            f"Confidence Interval (95%): ({result1.confidence_interval_95[0]:.3f}, {result1.confidence_interval_95[1]:.3f})"
        )
        print(f"Significant at alpha=0.05: {result1.is_significant_05}")
        print(
            f"Normality Group A (p-value): {result1.normality_p_value_group_a:.3f}"
        )
        print(
            f"Normality Group B (p-value): {result1.normality_p_value_group_b:.3f}"
        )
        print(f"Comment: {result1.comment}")
    except ValueError as e:
        print(f"Error: {e}")

    print("\n--- Test Case 2: Non-normal data ---")
    try:
        result2 = service.perform_t_test_analysis(
            group1_normal, group3_non_normal
        )
        print(f"Comment: {result2.comment}")
        print(f"P-Value: {result2.p_value:.3f}")
        print(
            f"Normality Group A (p-value): {result2.normality_p_value_group_a:.3f}"
        )
        print(
            f"Normality Group B (p-value): {result2.normality_p_value_group_b:.3f}"
        )
    except ValueError as e:
        print(f"Error: {e}")

    print("\n--- Test Case 3: Insufficient data for normality ---")
    try:
        service.perform_t_test_analysis(group4_small, group1_normal)
    except ValueError as e:
        print(f"Error: {e}")

    print(
        "\n--- Test Case 4: Identical constant groups (edge case for CI) ---"
    )
    group_const1 = [5.0, 5.0, 5.0, 5.0, 5.0]
    group_const2 = [5.0, 5.0, 5.0, 5.0, 5.0]
    try:
        result_const = service.perform_t_test_analysis(
            group_const1, group_const2
        )
        print(
            f"T-Statistic: {result_const.statistic}"
        )  # Should be 0 or nan by scipy
        print(
            f"P-Value: {result_const.p_value}"
        )  # Should be 1.0 or nan by scipy
        print(
            f"Confidence Interval (95%): {result_const.confidence_interval_95}"
        )
        print(f"Comment: {result_const.comment}")
    except ValueError as e:
        print(f"Error: {e}")

    print(
        "\n--- Test Case 5: Constant group vs Normal group (edge case for CI) ---"
    )
    try:
        result_const_normal = service.perform_t_test_analysis(
            group_const1, group1_normal
        )
        print(f"T-Statistic: {result_const_normal.statistic:.3f}")
        print(f"P-Value: {result_const_normal.p_value:.3f}")
        print(
            f"Confidence Interval (95%): ({result_const_normal.confidence_interval_95[0]:.3f}, {result_const_normal.confidence_interval_95[1]:.3f})"
        )
        print(f"Comment: {result_const_normal.comment}")
    except ValueError as e:
        print(f"Error: {e}")
