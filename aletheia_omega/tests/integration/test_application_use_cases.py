# aletheia_omega/tests/integration/test_application_use_cases.py

import pytest
import pickle
from unittest.mock import MagicMock

from sklearn.linear_model import LinearRegression, Ridge
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import Pipeline

from aletheia_omega.domain.entities import ModelRepresentation, ModelMetrics, OptimizationResult
from aletheia_omega.domain.services import (
    KolmogorovComplexityProxyService,
    LikelihoodService,
    OmegaCostService,
)
from aletheia_omega.application.use_cases import FindOptimalModelUseCase


# --- Fixtures para servicios reales ---
@pytest.fixture
def complexity_service() -> KolmogorovComplexityProxyService:
    return KolmogorovComplexityProxyService()

@pytest.fixture
def likelihood_service() -> LikelihoodService:
    # Usamos el servicio real ya que su comportamiento es crucial para el test
    return LikelihoodService()

@pytest.fixture
def omega_cost_service() -> OmegaCostService:
    return OmegaCostService()

# --- Fixture para el Caso de Uso con servicios reales ---
@pytest.fixture
def find_optimal_model_use_case(
    complexity_service, likelihood_service, omega_cost_service
) -> FindOptimalModelUseCase:
    return FindOptimalModelUseCase(
        complexity_service=complexity_service,
        likelihood_service=likelihood_service,
        omega_cost_service=omega_cost_service,
    )

# --- Datos y Modelos de Prueba ---
@pytest.fixture
def sample_data():
    # Datos simples para regresión
    X = [[i] for i in range(10)]  # Características
    y = [2 * i + 1 + (i % 2) * 0.5 - 0.25 for i in range(10)]  # Etiquetas con algo de ruido
    return X, y

@pytest.fixture
def model1_linear_regression(sample_data) -> ModelRepresentation:
    X, y = sample_data
    model = LinearRegression()
    model.fit(X, y)
    return ModelRepresentation(identifier="LinearRegression", content=pickle.dumps(model))

@pytest.fixture
def model2_polynomial_regression(sample_data) -> ModelRepresentation:
    X, y = sample_data
    model = Pipeline([
        ("poly_features", PolynomialFeatures(degree=3)),
        ("linear_regression", LinearRegression())
    ])
    model.fit(X, y)
    return ModelRepresentation(identifier="PolynomialRegression_Deg3", content=pickle.dumps(model))

@pytest.fixture
def model3_ridge_regression(sample_data) -> ModelRepresentation:
    X, y = sample_data
    model = Ridge(alpha=1.0)
    model.fit(X, y)
    return ModelRepresentation(identifier="RidgeRegression", content=pickle.dumps(model))

@pytest.fixture
def candidate_models_list(model1_linear_regression, model2_polynomial_regression, model3_ridge_regression):
    return [model1_linear_regression, model2_polynomial_regression, model3_ridge_regression]


class TestFindOptimalModelUseCaseIntegration:

    def test_execute_selects_best_model_based_on_mdl(
        self, find_optimal_model_use_case, candidate_models_list, sample_data
    ):
        lambda_param = 0.1  # Un lambda que podría favorecer modelos más precisos

        result = find_optimal_model_use_case.execute(
            candidate_models=candidate_models_list,
            data=sample_data,
            lambda_param=lambda_param,
            optimization_parameters={"source": "test_suite"}
        )

        assert isinstance(result, OptimizationResult)
        assert result.best_model is not None
        assert result.best_model_metrics is not None
        assert result.search_space_size == len(candidate_models_list)
        assert result.parameters == {"source": "test_suite"}

        # Verificar que las métricas del mejor modelo son consistentes
        # Recalculamos para el modelo elegido para asegurar la consistencia interna de la lógica
        # Esto es más una prueba de la correctitud del test en sí mismo y la expectativa.

        cs = find_optimal_model_use_case._complexity_service
        ls = find_optimal_model_use_case._likelihood_service
        ocs = find_optimal_model_use_case._omega_cost_service

        expected_complexity = cs.compute(result.best_model.content)
        expected_likelihood = ls.compute(result.best_model.content, sample_data)
        expected_mdl_cost = ocs.calculate_mdl_cost(
            expected_complexity, expected_likelihood, lambda_param
        )

        assert result.best_model_metrics.complexity == pytest.approx(expected_complexity)
        assert result.best_model_metrics.log_likelihood == pytest.approx(expected_likelihood)
        assert result.best_model_metrics.mdl_cost == pytest.approx(expected_mdl_cost)

        # Comprobar que el coste MDL del modelo elegido es el mínimo
        min_calculated_cost = float('inf')
        selected_model_id = result.best_model.identifier

        for model_repr in candidate_models_list:
            complexity = cs.compute(model_repr.content)
            log_likelihood = ls.compute(model_repr.content, sample_data)
            mdl_cost = ocs.calculate_mdl_cost(complexity, log_likelihood, lambda_param)

            if model_repr.identifier == selected_model_id:
                assert mdl_cost == pytest.approx(result.best_model_metrics.mdl_cost)

            if mdl_cost < min_calculated_cost:
                min_calculated_cost = mdl_cost

        assert result.best_model_metrics.mdl_cost == pytest.approx(min_calculated_cost)
        # No podemos saber de antemano cuál será el "mejor" sin ejecutarlo,
        # pero podemos asegurar que el resultado es consistente.
        # Por ejemplo, el modelo polinomial probablemente tendrá alta likelihood pero alta complejidad.
        # El lineal tendrá menor likelihood pero baja complejidad.
        # El resultado dependerá de lambda.

    def test_execute_with_no_candidate_models_raises_value_error(
        self, find_optimal_model_use_case, sample_data
    ):
        with pytest.raises(ValueError, match="La lista de modelos candidatos no puede estar vacía."):
            find_optimal_model_use_case.execute(
                candidate_models=[], data=sample_data, lambda_param=0.1
            )

    def test_execute_with_negative_lambda_raises_value_error(
        self, find_optimal_model_use_case, candidate_models_list, sample_data
    ):
        with pytest.raises(ValueError, match="El parámetro de regularización λ no puede ser negativo."):
            find_optimal_model_use_case.execute(
                candidate_models=candidate_models_list, data=sample_data, lambda_param=-0.1
            )

    def test_execute_calls_services_for_each_model(
        self, candidate_models_list, sample_data
    ):
        # Usamos Mocks para verificar interacciones con los servicios
        mock_complexity_service = MagicMock(spec=KolmogorovComplexityProxyService)
        mock_likelihood_service = MagicMock(spec=LikelihoodService)
        mock_omega_cost_service = MagicMock(spec=OmegaCostService)

        # Configurar los mocks para que devuelvan valores consistentes
        # Esto es importante para que el MDL cost sea calculable y comparable
        # y para que el test no falle por errores dentro de los mocks

        # Mockear compute de complexity service
        complexity_values = [10.0, 50.0, 15.0] # K(M1), K(M2), K(M3)
        mock_complexity_service.compute.side_effect = complexity_values

        # Mockear compute de likelihood service
        likelihood_values = [-2.0, -0.5, -1.8] # L(D|M1), L(D|M2), L(D|M3)
        mock_likelihood_service.compute.side_effect = likelihood_values

        # Mockear calculate_mdl_cost de omega_cost_service
        # Cost(M) = λ * K(M) - L(D|M)
        # λ = 0.5
        # M1: 0.5 * 10 - (-2.0) = 5 + 2.0 = 7.0
        # M2: 0.5 * 50 - (-0.5) = 25 + 0.5 = 25.5
        # M3: 0.5 * 15 - (-1.8) = 7.5 + 1.8 = 9.3
        # Expected best model is M1
        mdl_cost_values = [7.0, 25.5, 9.3]
        mock_omega_cost_service.calculate_mdl_cost.side_effect = mdl_cost_values

        use_case = FindOptimalModelUseCase(
            complexity_service=mock_complexity_service,
            likelihood_service=mock_likelihood_service,
            omega_cost_service=mock_omega_cost_service,
        )

        lambda_param = 0.5
        result = use_case.execute(
            candidate_models=candidate_models_list,
            data=sample_data,
            lambda_param=lambda_param
        )

        # Verificar llamadas a complexity_service
        assert mock_complexity_service.compute.call_count == len(candidate_models_list)
        for i, model_repr in enumerate(candidate_models_list):
            mock_complexity_service.compute.assert_any_call(model_repr.content)

        # Verificar llamadas a likelihood_service
        assert mock_likelihood_service.compute.call_count == len(candidate_models_list)
        for i, model_repr in enumerate(candidate_models_list):
            mock_likelihood_service.compute.assert_any_call(model_repr.content, sample_data)

        # Verificar llamadas a omega_cost_service
        assert mock_omega_cost_service.calculate_mdl_cost.call_count == len(candidate_models_list)
        for i in range(len(candidate_models_list)):
            mock_omega_cost_service.calculate_mdl_cost.assert_any_call(
                complexity=complexity_values[i],
                log_likelihood=likelihood_values[i],
                lambda_param=lambda_param,
            )

        # Verificar que el modelo correcto fue elegido (M1 en este caso)
        assert result.best_model.identifier == candidate_models_list[0].identifier
        assert result.best_model_metrics.mdl_cost == pytest.approx(mdl_cost_values[0])
        assert result.best_model_metrics.complexity == pytest.approx(complexity_values[0])
        assert result.best_model_metrics.log_likelihood == pytest.approx(likelihood_values[0])
        assert result.search_space_size == len(candidate_models_list)

    def test_all_models_fail_likelihood_computation(
        self, find_optimal_model_use_case, candidate_models_list, sample_data
    ):
        # Sobrescribir el servicio de likelihood para que siempre falle
        failing_likelihood_service = MagicMock(spec=LikelihoodService)
        # El valor de penalización definido en LikelihoodService
        failing_likelihood_service.compute.return_value = -1e9

        use_case = FindOptimalModelUseCase(
            complexity_service=find_optimal_model_use_case._complexity_service, # real
            likelihood_service=failing_likelihood_service, # mock
            omega_cost_service=find_optimal_model_use_case._omega_cost_service # real
        )

        lambda_param = 0.1
        result = use_case.execute(
            candidate_models=candidate_models_list,
            data=sample_data,
            lambda_param=lambda_param
        )

        # Todos los modelos tendrán un log_likelihood de -1e9.
        # El "mejor" será el que tenga la menor complejidad K(M),
        # ya que Cost(M) = λ * K(M) - (-1e9) = λ * K(M) + 1e9.
        # Para minimizar Cost(M), minimizamos K(M).

        cs = find_optimal_model_use_case._complexity_service
        complexities = {
            model.identifier: cs.compute(model.content) for model in candidate_models_list
        }

        min_complexity_identifier = min(complexities, key=complexities.get)

        assert result.best_model.identifier == min_complexity_identifier
        assert result.best_model_metrics.log_likelihood == -1e9
        assert result.best_model_metrics.complexity == pytest.approx(complexities[min_complexity_identifier])
        expected_mdl_cost = (lambda_param * complexities[min_complexity_identifier]) - (-1e9)
        assert result.best_model_metrics.mdl_cost == pytest.approx(expected_mdl_cost)

    def test_execute_with_unpicklable_model_in_likelihood_service(
        self, find_optimal_model_use_case, model1_linear_regression, sample_data
    ):
        # Este test usa el LikelihoodService real para asegurar que maneja errores de unpickling.

        # Crear un modelo con contenido corrupto
        corrupted_model = ModelRepresentation(
            identifier="CorruptedModel",
            content=b"esto no es un pickle valido"
        )

        candidate_models = [model1_linear_regression, corrupted_model]
        lambda_param = 0.1

        result = find_optimal_model_use_case.execute(
            candidate_models=candidate_models,
            data=sample_data,
            lambda_param=lambda_param
        )

        # El modelo corrupto debería ser penalizado fuertemente por LikelihoodService (-1e9)
        # Por lo tanto, el modelo lineal (asumiendo que es razonable) debería ser elegido.
        assert result.best_model.identifier == model1_linear_regression.identifier

        cs = find_optimal_model_use_case._complexity_service
        ls = find_optimal_model_use_case._likelihood_service # Real LikelihoodService
        ocs = find_optimal_model_use_case._omega_cost_service

        # Métricas para el modelo lineal
        lm_complexity = cs.compute(model1_linear_regression.content)
        lm_likelihood = ls.compute(model1_linear_regression.content, sample_data) # Debería ser un valor razonable
        lm_mdl_cost = ocs.calculate_mdl_cost(lm_complexity, lm_likelihood, lambda_param)

        # Métricas esperadas para el modelo corrupto
        corrupted_complexity = cs.compute(corrupted_model.content)
        corrupted_likelihood = -1e9 # Penalización del LikelihoodService
        corrupted_mdl_cost = ocs.calculate_mdl_cost(corrupted_complexity, corrupted_likelihood, lambda_param)

        assert lm_mdl_cost < corrupted_mdl_cost
        assert result.best_model_metrics.mdl_cost == pytest.approx(lm_mdl_cost)
        assert result.best_model_metrics.complexity == pytest.approx(lm_complexity)
        assert result.best_model_metrics.log_likelihood == pytest.approx(lm_likelihood)
        assert result.search_space_size == 2
