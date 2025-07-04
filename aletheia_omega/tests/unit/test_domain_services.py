# aletheia_omega/tests/unit/test_domain_services.py

import pickle
import pytest
from sklearn.linear_model import LinearRegression

from aletheia_omega.domain.services import (
    KolmogorovComplexityProxyService,
    LikelihoodService,
    OmegaCostService
)

# Definir NoScoreModel a nivel de módulo para que pickle pueda encontrarlo.
class NoScoreModel:
    def __init__(self):
        self.param = 5
    # No tiene método 'score'

@pytest.fixture
def complexity_service() -> KolmogorovComplexityProxyService:
    return KolmogorovComplexityProxyService()

@pytest.fixture
def likelihood_service() -> LikelihoodService:
    return LikelihoodService()

@pytest.fixture
def omega_cost_service() -> OmegaCostService:
    return OmegaCostService()


class TestKolmogorovComplexityProxyService:
    def test_complexity_of_simple_string(self, complexity_service):
        content = b"hello world"
        complexity = complexity_service.compute(content)
        assert complexity > 0
        assert isinstance(complexity, float)

    def test_complexity_more_complex_string_is_higher(self, complexity_service):
        simple_content = b"a" * 100
        complex_content = b"abcdefghijklmnopqrstuvwxyz0123456789" * 4

        complexity_simple = complexity_service.compute(simple_content)
        complexity_complex = complexity_service.compute(complex_content)

        assert complexity_complex > complexity_simple, \
               f"Complex: {complexity_complex}, Simple: {complexity_simple}"

    def test_complexity_empty_content_is_zero(self, complexity_service):
        assert complexity_service.compute(b"") == 0.0


class TestLikelihoodService:
    def test_likelihood_for_sklearn_model(self, likelihood_service):
        model = LinearRegression()
        X = [[0], [1], [2]]
        y = [0, 1, 2]
        model.fit(X, y)
        model_content = pickle.dumps(model)
        likelihood = likelihood_service.compute(model_content, (X, y))
        assert likelihood == pytest.approx(1.0)

    def test_likelihood_unsupported_model_is_penalized(self, likelihood_service):
        unsupported_model_content = pickle.dumps({"key": "a simple dict"})
        X = [[0]]
        y = [0]
        likelihood = likelihood_service.compute(unsupported_model_content, (X, y))
        assert likelihood == -1e9

    def test_likelihood_data_not_tuple_is_penalized(self, likelihood_service):
        model = LinearRegression()
        model_content = pickle.dumps(model)
        incorrect_data_format = "esto no es una tupla X,y" # Esto causará ValueError al desempaquetar
        likelihood = likelihood_service.compute(model_content, incorrect_data_format)
        assert likelihood == -1e9

    def test_likelihood_model_without_score_method_is_penalized(self, likelihood_service):
        model_no_score = NoScoreModel() # Usar la clase definida a nivel de módulo
        model_content = pickle.dumps(model_no_score)
        X = [[0]]
        y = [0]
        likelihood = likelihood_service.compute(model_content, (X,y))
        assert likelihood == -1e9


class TestOmegaCostService:
    def test_mdl_cost_calculation(self, omega_cost_service):
        cost = omega_cost_service.calculate_mdl_cost(
            complexity=20.0, log_likelihood=150.0, lambda_param=0.1
        )
        assert cost == pytest.approx(-148.0)

    def test_mdl_cost_high_lambda_penalizes_complexity(self, omega_cost_service):
        cost_simple = omega_cost_service.calculate_mdl_cost(
            complexity=10.0, log_likelihood=90.0, lambda_param=2.0
        )
        cost_complex = omega_cost_service.calculate_mdl_cost(
            complexity=50.0, log_likelihood=100.0, lambda_param=2.0
        )
        assert cost_simple < cost_complex

    def test_mdl_cost_low_lambda_prefers_precision(self, omega_cost_service):
        cost_simple = omega_cost_service.calculate_mdl_cost(
            complexity=10.0, log_likelihood=90.0, lambda_param=0.1
        )
        cost_complex = omega_cost_service.calculate_mdl_cost(
            complexity=50.0, log_likelihood=100.0, lambda_param=0.1
        )
        assert cost_complex < cost_simple

    def test_mdl_cost_negative_lambda_raises_error(self, omega_cost_service):
        with pytest.raises(ValueError):
            omega_cost_service.calculate_mdl_cost(10.0, 100.0, -0.5)
