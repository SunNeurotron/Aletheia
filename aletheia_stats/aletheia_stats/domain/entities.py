from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional
from uuid import UUID, uuid4
import datetime

@dataclass(frozen=True)
class TTestResult:
    """
    Represents the result of an independent two-sample t-test.

    Attributes:
        statistic: The calculated t-statistic.
        p_value: The two-tailed p-value.
        degrees_freedom: The degrees of freedom for the test (e.g., Welch's T-test).
        confidence_interval_95: Tuple representing the 95% confidence interval
                                for the difference in means.
        mean_group_a: Mean of group A.
        mean_group_b: Mean of group B;
        variance_group_a: Variance of group A.
        variance_group_b: Variance of group B.
        is_significant_05: True if p_value < 0.05, False otherwise.
        normality_p_value_group_a: P-value from Shapiro-Wilk test for group A.
        normality_p_value_group_b: P-value from Shapiro-Wilk test for group B.
        comment: Optional comment, e.g., if normality assumption was violated.
    """
    statistic: float
    p_value: float
    degrees_freedom: float
    confidence_interval_95: Tuple[float, float]
    mean_group_a: float
    mean_group_b: float
    variance_group_a: float
    variance_group_b: float
    is_significant_05: bool
    normality_p_value_group_a: float
    normality_p_value_group_b: float
    comment: Optional[str] = None


@dataclass
class Experiment:
    """
    Represents a statistical experiment, typically a t-test run.

    Attributes:
        id: Unique identifier for the experiment.
        name: Optional name for the experiment.
        description: Optional description of the experiment.
        group_a_data: Raw data for group A.
        group_b_data: Raw data for group B.
        parameters: Dictionary of parameters used for the test (e.g., alpha level).
        result: The TTestResult object.
        created_at: Timestamp of when the experiment was created.
        mlflow_run_id: Optional ID of the corresponding MLflow run.
    """
    id: UUID = field(default_factory=uuid4)
    name: Optional[str] = None
    description: Optional[str] = None
    group_a_data: List[float] = field(default_factory=list)
    group_b_data: List[float] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    result: Optional[TTestResult] = None
    created_at: datetime.datetime = field(default_factory=datetime.datetime.utcnow)
    mlflow_run_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converts the experiment to a dictionary, useful for serialization."""
        res_dict = self.result.__dict__ if self.result else None
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "group_a_data": self.group_a_data,
            "group_b_data": self.group_b_data,
            "parameters": self.parameters,
            "result": res_dict,
            "created_at": self.created_at.isoformat(),
            "mlflow_run_id": self.mlflow_run_id,
        }

# Example usage (optional, for testing or demonstration)
if __name__ == "__main__":
    # Create a sample TTestResult
    sample_ttest_result = TTestResult(
        statistic=2.1,
        p_value=0.045,
        degrees_freedom=38.5,
        confidence_interval_95=(0.1, 1.9),
        mean_group_a=5.5,
        mean_group_b=4.5,
        variance_group_a=1.2,
        variance_group_b=1.3,
        is_significant_05=True,
        normality_p_value_group_a=0.56,
        normality_p_value_group_b=0.67,
        comment="Sample groups appear normally distributed."
    )
    print(f"Sample TTestResult: {sample_ttest_result}")

    # Create a sample Experiment
    sample_experiment = Experiment(
        name="Sample T-Test Experiment",
        description="A demonstration of the Experiment data class.",
        group_a_data=[1.0, 2.0, 3.0, 4.0, 5.0],
        group_b_data=[2.0, 3.0, 4.0, 5.0, 6.0],
        parameters={"alpha": 0.05, "test_type": "Welch's t-test"},
        result=sample_ttest_result,
    )
    print(f"Sample Experiment (dict): {sample_experiment.to_dict()}")
    print(f"Sample Experiment ID: {sample_experiment.id}")
    print(f"Sample Experiment MLflow Run ID: {sample_experiment.mlflow_run_id}")
