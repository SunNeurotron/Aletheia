# aletheia_omega/tests/unit/test_domain_services.py

import pickle
import pytest
import uuid # Necesario para los IDs de trayectoria
from sklearn.linear_model import LinearRegression

from aletheia_omega.domain.services import (
    KolmogorovComplexityProxyService,
    LikelihoodService,
    OmegaCostService,
    TrajectoryAnalysisService # Importar el nuevo servicio
)
from aletheia_omega.domain.entities import (
    ModelRepresentation,
    ModelMetrics,
    Trajectory,         # Importar entidades de trayectoria
    TrajectoryStep,
    TrajectoryState,
    TrajectoryAnalysis
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

@pytest.fixture
def trajectory_analysis_service() -> TrajectoryAnalysisService:
    return TrajectoryAnalysisService()

# --- Fixtures para ayudar a crear datos de prueba para trayectorias ---
@pytest.fixture
def sample_model_repr_1() -> ModelRepresentation:
    return ModelRepresentation(identifier="model_A", content=b"content_A")

@pytest.fixture
def sample_model_repr_2() -> ModelRepresentation:
    return ModelRepresentation(identifier="model_B", content=b"content_B")

@pytest.fixture
def sample_model_repr_3() -> ModelRepresentation:
    return ModelRepresentation(identifier="model_C", content=b"content_C")

@pytest.fixture
def sample_metrics_1() -> ModelMetrics:
    return ModelMetrics(complexity=10.0, log_likelihood=100.0, mdl_cost=-90.0) # C = 10*L - K

@pytest.fixture
def sample_metrics_2() -> ModelMetrics:
    return ModelMetrics(complexity=20.0, log_likelihood=120.0, mdl_cost=-100.0)

@pytest.fixture
def sample_metrics_3() -> ModelMetrics:
    return ModelMetrics(complexity=5.0, log_likelihood=90.0, mdl_cost=-85.0)


class TestKolmogorovComplexityProxyService:
    # ... (tests existentes sin cambios) ...
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
    # ... (tests existentes sin cambios) ...
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
        incorrect_data_format = "esto no es una tupla X,y"
        likelihood = likelihood_service.compute(model_content, incorrect_data_format)
        assert likelihood == -1e9

    def test_likelihood_model_without_score_method_is_penalized(self, likelihood_service):
        model_no_score = NoScoreModel()
        model_content = pickle.dumps(model_no_score)
        X = [[0]]
        y = [0]
        likelihood = likelihood_service.compute(model_content, (X,y))
        assert likelihood == -1e9

class TestOmegaCostService:
    # ... (tests existentes sin cambios) ...
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


class TestTrajectoryAnalysisService:
    MIN_STEPS = TrajectoryAnalysisService.MIN_STEPS_FOR_ANALYSIS

    def test_analyze_null_trajectory_raises_error(self, trajectory_analysis_service):
        with pytest.raises(ValueError, match="Se intentó analizar una trayectoria nula."):
            trajectory_analysis_service.analyze(None)

    def test_analyze_empty_trajectory_is_undefined(self, trajectory_analysis_service):
        trajectory = Trajectory(id=uuid.uuid4(), name="Empty Trajectory", steps=[])
        analysis = trajectory_analysis_service.analyze(trajectory)
        assert analysis.state == TrajectoryState.UNDEFINED
        assert analysis.step_count == 0
        assert "vacía o no tiene pasos" in analysis.comment

    def test_analyze_trajectory_too_short_is_undefined(self, trajectory_analysis_service, sample_model_repr_1, sample_metrics_1):
        steps = [
            TrajectoryStep(step_index=i, model=sample_model_repr_1, metrics=sample_metrics_1)
            for i in range(self.MIN_STEPS - 1)
        ]
        trajectory = Trajectory(id=uuid.uuid4(), name="Short Trajectory", steps=steps)
        analysis = trajectory_analysis_service.analyze(trajectory)
        assert analysis.state == TrajectoryState.UNDEFINED
        assert analysis.step_count == len(steps)
        assert f"Se requieren al menos {self.MIN_STEPS} pasos" in analysis.comment

    def test_analyze_stationary_trajectory(
        self, trajectory_analysis_service, sample_model_repr_1, sample_model_repr_2, sample_metrics_1, sample_metrics_2
    ):
        # Construir una trayectoria donde los últimos N/3 modelos son idénticos (model_A)
        # y N >= MIN_STEPS_FOR_ANALYSIS
        # ej. MIN_STEPS = 5. tail_size = 5//3 = 1. No es suficiente para la heurística.
        # Necesitamos que tail_size sea representativo. El servicio usa max(1, count//3).
        # Si MIN_STEPS = 5, tail_size = 1.
        # Para que la lógica de 'cola' sea robusta, necesitamos más pasos.
        # Usemos 6 pasos para que tail_size sea 2.
        num_steps = max(self.MIN_STEPS, 6) # Asegurar suficientes pasos para que tail_size >= 2

        steps = []
        # Primeros pasos variados
        for i in range(num_steps - 2): # Deja los últimos 2 para ser idénticos
            model = sample_model_repr_2 if i % 2 == 0 else sample_model_repr_1
            metrics = sample_metrics_2 if i % 2 == 0 else sample_metrics_1
            steps.append(TrajectoryStep(step_index=i, model=model, metrics=metrics))

        # Últimos pasos idénticos (model_A)
        for i in range(num_steps - 2, num_steps):
            steps.append(TrajectoryStep(step_index=i, model=sample_model_repr_1, metrics=sample_metrics_1))

        trajectory = Trajectory(id=uuid.uuid4(), name="Stationary Trajectory", steps=steps)
        analysis = trajectory_analysis_service.analyze(trajectory)

        assert analysis.state == TrajectoryState.STATIONARY
        assert analysis.step_count == num_steps
        assert f"convergido al modelo '{sample_model_repr_1.identifier}'" in analysis.comment

    def test_analyze_oscillatory_trajectory(
        self, trajectory_analysis_service, sample_model_repr_1, sample_model_repr_2, sample_metrics_1, sample_metrics_2
    ):
        # Construir una trayectoria donde los últimos MIN_STEPS modelos oscilan entre A y B
        steps = []
        # Relleno inicial si MIN_STEPS es mayor, para asegurar que no sea estacionaria antes
        for i in range(max(0, self.MIN_STEPS - 3)): # algunos modelos diferentes al principio
             steps.append(TrajectoryStep(step_index=i, model=ModelRepresentation(identifier=f"filler_{i}", content=b"f"), metrics=sample_metrics_1))

        current_len = len(steps)
        for i in range(self.MIN_STEPS):
            model = sample_model_repr_1 if i % 2 == 0 else sample_model_repr_2
            metrics = sample_metrics_1 if i % 2 == 0 else sample_metrics_2
            steps.append(TrajectoryStep(step_index=current_len + i, model=model, metrics=metrics))

        trajectory = Trajectory(id=uuid.uuid4(), name="Oscillatory Trajectory", steps=steps)
        analysis = trajectory_analysis_service.analyze(trajectory)

        assert analysis.state == TrajectoryState.OSCILLATORY
        assert analysis.step_count == len(steps)
        # Aserciones robustas para el comentario
        comment_lower = analysis.comment.lower()
        assert "oscila" in comment_lower
        assert "entre los modelos" in comment_lower
        # Verificar la presencia de los identificadores de modelo, sin importar el orden en el set
        assert sample_model_repr_1.identifier in analysis.comment # El comment original tiene los identificadores
        assert sample_model_repr_2.identifier in analysis.comment

    def test_analyze_progressive_trajectory(
        self, trajectory_analysis_service, sample_metrics_1
    ):
        # Construir una trayectoria donde los modelos son siempre diferentes
        steps = []
        for i in range(self.MIN_STEPS):
            model = ModelRepresentation(identifier=f"model_v{i}", content=f"content_v{i}".encode())
            steps.append(TrajectoryStep(step_index=i, model=model, metrics=sample_metrics_1))

        trajectory = Trajectory(id=uuid.uuid4(), name="Progressive Trajectory", steps=steps)
        analysis = trajectory_analysis_service.analyze(trajectory)

        assert analysis.state == TrajectoryState.PROGRESSIVE
        assert analysis.step_count == self.MIN_STEPS
        assert "explorando nuevos modelos" in analysis.comment

    def test_analyze_stationary_longer_tail(
        self, trajectory_analysis_service, sample_model_repr_1, sample_metrics_1
    ):
        # 9 pasos, tail_size será 3. Todos los últimos 3 son model_A.
        steps = [
            TrajectoryStep(step_index=0, model=ModelRepresentation(identifier="X", content=b"X"), metrics=sample_metrics_1),
            TrajectoryStep(step_index=1, model=ModelRepresentation(identifier="Y", content=b"Y"), metrics=sample_metrics_1),
            TrajectoryStep(step_index=2, model=ModelRepresentation(identifier="Z", content=b"Z"), metrics=sample_metrics_1),
            TrajectoryStep(step_index=3, model=ModelRepresentation(identifier="X", content=b"X"), metrics=sample_metrics_1),
            TrajectoryStep(step_index=4, model=ModelRepresentation(identifier="Y", content=b"Y"), metrics=sample_metrics_1),
            TrajectoryStep(step_index=5, model=ModelRepresentation(identifier="Z", content=b"Z"), metrics=sample_metrics_1),
            TrajectoryStep(step_index=6, model=sample_model_repr_1, metrics=sample_metrics_1),
            TrajectoryStep(step_index=7, model=sample_model_repr_1, metrics=sample_metrics_1),
            TrajectoryStep(step_index=8, model=sample_model_repr_1, metrics=sample_metrics_1),
        ]
        trajectory = Trajectory(id=uuid.uuid4(), name="Stationary Long Trajectory", steps=steps)
        analysis = trajectory_analysis_service.analyze(trajectory)
        assert analysis.state == TrajectoryState.STATIONARY

    def test_analyze_oscillatory_three_models_in_recent_is_progressive(
        self, trajectory_analysis_service, sample_model_repr_1, sample_model_repr_2, sample_model_repr_3, sample_metrics_1
    ):
        # Si hay 3 modelos únicos en la ventana reciente, la heurística actual lo clasifica como progresivo.
        steps = []
        # Asegurar MIN_STEPS
        for i in range(self.MIN_STEPS):
            if i % 3 == 0: model = sample_model_repr_1
            elif i % 3 == 1: model = sample_model_repr_2
            else: model = sample_model_repr_3
            steps.append(TrajectoryStep(step_index=i, model=model, metrics=sample_metrics_1))

        trajectory = Trajectory(id=uuid.uuid4(), name="Oscillatory? Or Progressive Trajectory", steps=steps)
        analysis = trajectory_analysis_service.analyze(trajectory)

        assert analysis.state == TrajectoryState.PROGRESSIVE # Porque len(unique_recent_models) es 3
        assert "explorando nuevos modelos" in analysis.comment
