# aletheia_omega/tests/unit/test_domain_services.py

import pickle
import pytest
from sklearn.linear_model import LinearRegression

from aletheia_omega.domain.services import (
    KolmogorovComplexityProxyService,
    LikelihoodService,
    OmegaCostService
)
# No es necesario ModelRepresentation aquí si no se usa directamente en los tests unitarios de servicios.
# from aletheia_omega.domain.entities import ModelRepresentation


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
        # "a" * 100 es muy compresible.
        simple_content = b"a" * 100
        # Una cadena con más variedad de caracteres debería ser menos compresible.
        # Se multiplica para asegurar que sea suficientemente larga para que gzip muestre diferencias.
        complex_content = b"abcdefghijklmnopqrstuvwxyz0123456789" * 4

        complexity_simple = complexity_service.compute(simple_content)
        complexity_complex = complexity_service.compute(complex_content)

        # La expectativa es que el contenido más diverso y menos repetitivo
        # resulte en una longitud mayor después de la compresión.
        assert complexity_complex > complexity_simple, \
               f"Complex: {complexity_complex}, Simple: {complexity_simple}"


    def test_complexity_empty_content_is_zero(self, complexity_service):
        assert complexity_service.compute(b"") == 0.0


class TestLikelihoodService:
    def test_likelihood_for_sklearn_model(self, likelihood_service):
        # 1. Crear y serializar un modelo de ejemplo
        model = LinearRegression()
        X = [[0], [1], [2]]
        y = [0, 1, 2]
        model.fit(X, y)
        model_content = pickle.dumps(model)

        # 2. Calcular la verosimilitud (score en este caso)
        likelihood = likelihood_service.compute(model_content, (X, y))

        # Un modelo perfecto en estos datos tendrá un score de 1.0
        assert likelihood == pytest.approx(1.0)

    def test_likelihood_unsupported_model_is_penalized(self, likelihood_service):
        # Un diccionario no tiene método 'score' y causará AttributeError o similar.
        unsupported_model_content = pickle.dumps({"key": "a simple dict"})
        X = [[0]]
        y = [0]

        likelihood = likelihood_service.compute(unsupported_model_content, (X, y))

        assert likelihood == -1e9 # Penalización por error de deserialización/uso

    def test_likelihood_data_not_tuple_is_penalized(self, likelihood_service):
        model = LinearRegression()
        # No es necesario entrenar el modelo para este test, solo necesitamos su contenido serializado
        # y que sea un objeto que normalmente tendría un método 'score'.
        model_content = pickle.dumps(model)

        # Proporcionar datos en un formato incorrecto (no una tupla X, y)
        # Esto debería causar un TypeError dentro del servicio al intentar desempaquetar.
        incorrect_data_format = "esto no es una tupla X,y"

        likelihood = likelihood_service.compute(model_content, incorrect_data_format)
        assert likelihood == -1e9

    def test_likelihood_model_without_score_method_is_penalized(self, likelihood_service):
        # Crear un objeto que se puede serializar con pickle pero no tiene el método 'score'
        class NoScoreModel:
            def __init__(self):
                self.param = 5
            # No tiene método 'score'

        model_no_score = NoScoreModel()
        model_content = pickle.dumps(model_no_score)
        X = [[0]] # Datos de ejemplo, no se usarán si 'score' no existe
        y = [0]

        # Esto debería causar un NotImplementedError o AttributeError dentro del servicio.
        likelihood = likelihood_service.compute(model_content, (X,y))
        assert likelihood == -1e9


class TestOmegaCostService:
    def test_mdl_cost_calculation(self, omega_cost_service):
        cost = omega_cost_service.calculate_mdl_cost(
            complexity=20.0, log_likelihood=150.0, lambda_param=0.1
        )
        # Coste = 0.1 * 20 - 150 = 2 - 150 = -148
        assert cost == pytest.approx(-148.0)

    def test_mdl_cost_high_lambda_penalizes_complexity(self, omega_cost_service):
        # Modelo simple pero menos preciso
        cost_simple = omega_cost_service.calculate_mdl_cost(
            complexity=10.0, log_likelihood=90.0, lambda_param=2.0
        ) # Coste = 2*10 - 90 = -70

        # Modelo complejo pero más preciso
        cost_complex = omega_cost_service.calculate_mdl_cost(
            complexity=50.0, log_likelihood=100.0, lambda_param=2.0
        ) # Coste = 2*50 - 100 = 0

        # Con un lambda alto, el modelo simple es preferido (coste más bajo)
        assert cost_simple < cost_complex

    def test_mdl_cost_low_lambda_prefers_precision(self, omega_cost_service):
        # Modelo simple pero menos preciso
        cost_simple = omega_cost_service.calculate_mdl_cost(
            complexity=10.0, log_likelihood=90.0, lambda_param=0.1
        ) # Coste = 0.1*10 - 90 = -89

        # Modelo complejo pero más preciso
        cost_complex = omega_cost_service.calculate_mdl_cost(
            complexity=50.0, log_likelihood=100.0, lambda_param=0.1
        ) # Coste = 0.1*50 - 100 = -95

        # Con un lambda bajo, el modelo complejo es preferido (coste más bajo)
        assert cost_complex < cost_simple

    def test_mdl_cost_negative_lambda_raises_error(self, omega_cost_service):
        with pytest.raises(ValueError):
            omega_cost_service.calculate_mdl_cost(10.0, 100.0, -0.5)
