from datetime import datetime, timezone
from unittest.mock import MagicMock, call  # Import 'call' for checking call arguments
from uuid import UUID, uuid4

import pytest
import sqlalchemy as sa  # For sa.func in count query mock
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from aletheia_stats.aletheia_stats.domain.entities import Experiment as DomainExperiment
from aletheia_stats.aletheia_stats.domain.entities import (
    TTestResult as DomainTTestResult,
)
from aletheia_stats.aletheia_stats.infrastructure.models import (
    ExperimentModel,
    TTestResultModel,
)

# Objetos a probar y sus dependencias
from aletheia_stats.aletheia_stats.infrastructure.sqlalchemy_repository import (
    SQLAlchemyStatsRepository,
)

# --- Fixtures ---


@pytest.fixture
def mock_db_session() -> MagicMock:
    """Fixture para mockear una sesión de SQLAlchemy."""
    session = MagicMock(spec=Session)
    # Configurar mocks para los métodos de query encadenados
    # query().filter().first()
    # query().scalar()
    # query().order_by().offset().limit().all()

    # Mock para query() que devuelve un objeto que puede ser encadenado
    mock_query_obj = MagicMock()
    session.query.return_value = mock_query_obj

    # Configurar filter().first()
    mock_filter_obj = MagicMock()
    mock_query_obj.filter.return_value = mock_filter_obj
    mock_filter_obj.first.return_value = None  # Default: no encontrado

    # Configurar scalar() para el conteo
    # mock_query_obj.scalar.return_value = 0 # Default: 0 items
    # Need to handle different types of query().scalar() calls
    # For count: query(func.count(...)).scalar()
    # For other single results: query(...).filter(...).scalar()
    # We can make the default scalar more flexible or set it per test.
    # For now, the specific count query mock is handled in test_list_all_experiments_returns_list_and_count.

    # Configurar order_by().offset().limit().all()
    mock_orderby_obj = MagicMock()
    mock_query_obj.order_by.return_value = mock_orderby_obj
    mock_offset_obj = MagicMock()
    mock_orderby_obj.offset.return_value = mock_offset_obj
    mock_limit_obj = MagicMock()
    mock_offset_obj.limit.return_value = mock_limit_obj
    mock_limit_obj.all.return_value = []  # Default: lista vacía

    return session


@pytest.fixture
def stats_repository(mock_db_session: MagicMock) -> SQLAlchemyStatsRepository:
    """Fixture para instanciar el repositorio con la sesión mockeada."""
    return SQLAlchemyStatsRepository(db=mock_db_session)


@pytest.fixture
def sample_ttest_result_domain() -> DomainTTestResult:
    """Un objeto DomainTTestResult de ejemplo."""
    return DomainTTestResult(
        statistic=2.0,
        p_value=0.05,
        degrees_freedom=30.0,
        mean_group_a=10.0,
        variance_group_a=2.0,
        mean_group_b=8.0,
        variance_group_b=1.5,
        confidence_interval_95=[0.1, 3.9],
        is_significant_05=True,
        normality_p_value_group_a=0.5,
        normality_p_value_group_b=0.6,
        comment="Sample result",
    )


@pytest.fixture
def sample_experiment_domain(
    sample_ttest_result_domain: DomainTTestResult,
) -> DomainExperiment:
    """Un objeto DomainExperiment de ejemplo."""
    return DomainExperiment(
        id=uuid4(),
        name="Test Experiment",
        description="A test experiment",
        group_a_data=[1.0, 2.0, 3.0],
        group_b_data=[4.0, 5.0, 6.0],
        parameters={"alpha": 0.05},
        result=sample_ttest_result_domain,
        mlflow_run_id="mlflow_123",
        tracking_warnings=["MLflow down"],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_experiment_model(
    sample_experiment_domain: DomainExperiment,
) -> ExperimentModel:
    """Un objeto ExperimentModel de ejemplo, derivado del DomainExperiment."""
    result_model = None
    if sample_experiment_domain.result:
        result_model = TTestResultModel(
            id=uuid4(),
            experiment_id=sample_experiment_domain.id,
            statistic=sample_experiment_domain.result.statistic,
            p_value=sample_experiment_domain.result.p_value,
            degrees_freedom=sample_experiment_domain.result.degrees_freedom,
            mean_group_a=sample_experiment_domain.result.mean_group_a,
            variance_group_a=sample_experiment_domain.result.variance_group_a,
            mean_group_b=sample_experiment_domain.result.mean_group_b,
            variance_group_b=sample_experiment_domain.result.variance_group_b,
            confidence_interval_95_lower=sample_experiment_domain.result.confidence_interval_95[
                0
            ],
            confidence_interval_95_upper=sample_experiment_domain.result.confidence_interval_95[
                1
            ],
            is_significant_05=sample_experiment_domain.result.is_significant_05,
            normality_p_value_group_a=sample_experiment_domain.result.normality_p_value_group_a,
            normality_p_value_group_b=sample_experiment_domain.result.normality_p_value_group_b,
            comment=sample_experiment_domain.result.comment,
        )

    return ExperimentModel(
        id=sample_experiment_domain.id,
        name=sample_experiment_domain.name,
        description=sample_experiment_domain.description,
        group_a_data=sample_experiment_domain.group_a_data,
        group_b_data=sample_experiment_domain.group_b_data,
        parameters=sample_experiment_domain.parameters,
        mlflow_run_id=sample_experiment_domain.mlflow_run_id,
        tracking_warnings=sample_experiment_domain.tracking_warnings,
        created_at=sample_experiment_domain.created_at,
        updated_at=sample_experiment_domain.updated_at,
        result_model=result_model,
    )


# --- Pruebas ---


def test_save_new_experiment(
    stats_repository: SQLAlchemyStatsRepository,
    mock_db_session: MagicMock,
    sample_experiment_domain: DomainExperiment,
):
    mock_db_session.query(ExperimentModel).filter().first.return_value = None
    saved_experiment = stats_repository.save(sample_experiment_domain)
    mock_db_session.add.assert_called_once()
    added_object = mock_db_session.add.call_args[0][0]
    assert isinstance(added_object, ExperimentModel)
    assert added_object.id == sample_experiment_domain.id
    assert added_object.name == sample_experiment_domain.name
    assert (
        added_object.tracking_warnings
        == sample_experiment_domain.tracking_warnings
    )
    if sample_experiment_domain.result:
        assert added_object.result_model is not None
        assert (
            added_object.result_model.p_value
            == sample_experiment_domain.result.p_value
        )
    mock_db_session.commit.assert_called_once()
    assert mock_db_session.refresh.call_count >= 1
    mock_db_session.refresh.assert_any_call(added_object)
    if added_object.result_model:
        mock_db_session.refresh.assert_any_call(added_object.result_model)
    assert saved_experiment.id == sample_experiment_domain.id
    assert saved_experiment.name == sample_experiment_domain.name
    assert (
        saved_experiment.tracking_warnings
        == sample_experiment_domain.tracking_warnings
    )


def test_save_update_existing_experiment(
    stats_repository: SQLAlchemyStatsRepository,
    mock_db_session: MagicMock,
    sample_experiment_domain: DomainExperiment,
    sample_experiment_model: ExperimentModel,
):
    mock_db_session.query(ExperimentModel).filter().first.return_value = (
        sample_experiment_model
    )
    updated_experiment_domain = sample_experiment_domain.copy(deep=True)
    updated_experiment_domain.name = "Updated Experiment Name"
    updated_experiment_domain.add_tracking_warning("Update warning")
    if updated_experiment_domain.result:
        updated_experiment_domain.result.comment = "Updated comment"
    saved_experiment = stats_repository.save(updated_experiment_domain)
    mock_db_session.add.assert_called_once_with(sample_experiment_model)
    assert sample_experiment_model.name == "Updated Experiment Name"
    assert "Update warning" in sample_experiment_model.tracking_warnings
    if (
        sample_experiment_model.result_model
        and updated_experiment_domain.result
    ):
        assert (
            sample_experiment_model.result_model.comment == "Updated comment"
        )
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_any_call(sample_experiment_model)
    if sample_experiment_model.result_model:
        mock_db_session.refresh.assert_any_call(
            sample_experiment_model.result_model
        )
    assert saved_experiment.name == "Updated Experiment Name"
    assert "Update warning" in saved_experiment.tracking_warnings


def test_save_handles_sqlalchemy_error(
    stats_repository: SQLAlchemyStatsRepository,
    mock_db_session: MagicMock,
    sample_experiment_domain: DomainExperiment,
):
    mock_db_session.commit.side_effect = SQLAlchemyError("Simulated DB error")
    with pytest.raises(SQLAlchemyError):
        stats_repository.save(sample_experiment_domain)
    mock_db_session.rollback.assert_called_once()


def test_get_experiment_found(
    stats_repository: SQLAlchemyStatsRepository,
    mock_db_session: MagicMock,
    sample_experiment_model: ExperimentModel,
    sample_experiment_domain: DomainExperiment,
):
    experiment_id_to_find = sample_experiment_model.id
    mock_db_session.query(ExperimentModel).filter().first.return_value = (
        sample_experiment_model
    )
    retrieved_experiment = stats_repository.get(experiment_id_to_find)
    mock_db_session.query(ExperimentModel).filter.assert_called_once()
    assert retrieved_experiment is not None
    assert retrieved_experiment.id == experiment_id_to_find
    assert retrieved_experiment.name == sample_experiment_domain.name
    assert (
        retrieved_experiment.tracking_warnings
        == sample_experiment_domain.tracking_warnings
    )
    if sample_experiment_domain.result:
        assert retrieved_experiment.result is not None
        assert (
            retrieved_experiment.result.p_value
            == sample_experiment_domain.result.p_value
        )
        assert (
            retrieved_experiment.result.confidence_interval_95
            == sample_experiment_domain.result.confidence_interval_95
        )
    else:
        assert retrieved_experiment.result is None


def test_get_experiment_not_found(
    stats_repository: SQLAlchemyStatsRepository, mock_db_session: MagicMock
):
    experiment_id_not_found = uuid4()
    mock_db_session.query(ExperimentModel).filter().first.return_value = None
    retrieved_experiment = stats_repository.get(experiment_id_not_found)
    assert retrieved_experiment is None
    mock_db_session.query(ExperimentModel).filter.assert_called_once()


def test_get_handles_sqlalchemy_error(
    stats_repository: SQLAlchemyStatsRepository, mock_db_session: MagicMock
):
    experiment_id_error = uuid4()
    mock_db_session.query(ExperimentModel).filter().first.side_effect = (
        SQLAlchemyError("Simulated DB error on get")
    )
    with pytest.raises(SQLAlchemyError):
        stats_repository.get(experiment_id_error)
    mock_db_session.query(ExperimentModel).filter.assert_called_once()


def test_list_all_experiments_returns_list_and_count(
    stats_repository: SQLAlchemyStatsRepository,
    mock_db_session: MagicMock,
    sample_experiment_model: ExperimentModel,
):
    model1 = sample_experiment_model
    model2_id = uuid4()
    model2 = ExperimentModel(
        id=model2_id,
        name="Experiment 2",
        group_a_data=[0],
        group_b_data=[1],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    mock_experiment_models = [model1, model2]
    expected_total_count = 5

    # Mock for query(func.count(...)).scalar()
    count_query_mock = MagicMock()
    mock_db_session.query.return_value = count_query_mock  # Default query mock
    count_query_mock.scalar.return_value = expected_total_count

    # Mock for query(ExperimentModel).order_by()...
    list_query_mock = MagicMock()  # Separate mock for the list query chain
    mock_filter_obj_list = MagicMock()
    list_query_mock.order_by.return_value = mock_filter_obj_list
    mock_offset_obj_list = MagicMock()
    mock_filter_obj_list.offset.return_value = mock_offset_obj_list
    mock_limit_obj_list = MagicMock()
    mock_offset_obj_list.limit.return_value = mock_limit_obj_list
    mock_limit_obj_list.all.return_value = mock_experiment_models

    # Configure session.query to return different mocks based on args
    def query_side_effect(*args, **kwargs):
        if args and isinstance(
            args[0], type(sa.func.count(ExperimentModel.id))
        ):  # Check if it's a count query
            return count_query_mock
        return list_query_mock  # Default to list query mock

    mock_db_session.query.side_effect = query_side_effect

    skip, limit = 0, 2
    domain_experiments, total_count = stats_repository.list_all(
        skip=skip, limit=limit
    )

    assert total_count == expected_total_count
    assert len(domain_experiments) == len(mock_experiment_models)
    assert isinstance(domain_experiments[0], DomainExperiment)
    assert domain_experiments[0].id == model1.id
    assert domain_experiments[1].id == model2.id

    list_query_mock.order_by().offset.assert_called_once_with(skip)
    list_query_mock.order_by().offset().limit.assert_called_once_with(limit)


def test_list_all_empty(
    stats_repository: SQLAlchemyStatsRepository, mock_db_session: MagicMock
):
    mock_db_session.query(
        sa.func.count(ExperimentModel.id)
    ).scalar.return_value = 0
    mock_db_session.query(
        ExperimentModel
    ).order_by().offset().limit().all.return_value = []
    domain_experiments, total_count = stats_repository.list_all()
    assert total_count == 0
    assert len(domain_experiments) == 0


def test_list_all_handles_sqlalchemy_error(
    stats_repository: SQLAlchemyStatsRepository, mock_db_session: MagicMock
):
    mock_db_session.query(
        sa.func.count(ExperimentModel.id)
    ).scalar.side_effect = SQLAlchemyError("Simulated DB error on count")
    with pytest.raises(SQLAlchemyError):
        stats_repository.list_all()

    mock_db_session.query(
        sa.func.count(ExperimentModel.id)
    ).scalar.side_effect = None
    mock_db_session.query(
        sa.func.count(ExperimentModel.id)
    ).scalar.return_value = 1
    mock_db_session.query(
        ExperimentModel
    ).order_by().offset().limit().all.side_effect = SQLAlchemyError(
        "Simulated DB error on list"
    )
    with pytest.raises(SQLAlchemyError):
        stats_repository.list_all()


def test_placeholder():
    assert True
