import logging
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import create_engine, Column, String, JSON, DateTime, Float, Boolean, Tuple as SQLTuple # Renamed Tuple to avoid conflict
from sqlalchemy.orm import sessionmaker, Session as SQLAlchemySession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID as PG_UUID # For PostgreSQL UUID type
import datetime

from ..domain.entities import Experiment, TTestResult # Domain entities
from ..domain.ports import StatsRepository # Abstract port

logger = logging.getLogger(__name__)

Base = declarative_base()

# --- SQLAlchemy Models ---
class TTestResultDB(Base): # type: ignore
    """
    SQLAlchemy model for storing TTestResult data.
    This is part of an ExperimentDB model, typically stored as JSON or separate columns.
    For simplicity here, we'll assume it's stored as JSON within ExperimentDB,
    but if direct querying on TTestResult fields were needed, it would be a separate table.
    This class definition is more for ORM mapping if it were a separate table.
    """
    __tablename__ = "ttest_results" # Example if it were a separate table

    # If it were a separate table, it would need its own primary key and a foreign key to ExperimentDB
    id = Column(PG_UUID(as_uuid=True), primary_key=True) # Example PK
    experiment_id = Column(PG_UUID(as_uuid=True)) # Example FK, needs index and ForeignKeyConstraint

    statistic = Column(Float, nullable=False)
    p_value = Column(Float, nullable=False)
    degrees_freedom = Column(Float, nullable=False)
    # Storing a tuple (confidence_interval_95) can be tricky. JSON is often easiest.
    # Alternatively, two Float columns: ci_95_lower, ci_95_upper
    confidence_interval_95_lower = Column(Float)
    confidence_interval_95_upper = Column(Float)
    mean_group_a = Column(Float)
    mean_group_b = Column(Float)
    variance_group_a = Column(Float)
    variance_group_b = Column(Float)
    is_significant_05 = Column(Boolean)
    normality_p_value_group_a = Column(Float)
    normality_p_value_group_b = Column(Float)
    comment = Column(String, nullable=True)

    def to_domain(self) -> TTestResult:
        return TTestResult(
            statistic=self.statistic,
            p_value=self.p_value,
            degrees_freedom=self.degrees_freedom,
            confidence_interval_95=(self.confidence_interval_95_lower, self.confidence_interval_95_upper),
            mean_group_a=self.mean_group_a,
            mean_group_b=self.mean_group_b,
            variance_group_a=self.variance_group_a,
            variance_group_b=self.variance_group_b,
            is_significant_05=self.is_significant_05,
            normality_p_value_group_a=self.normality_p_value_group_a,
            normality_p_value_group_b=self.normality_p_value_group_b,
            comment=self.comment
        )

    @staticmethod
    def from_domain(domain_obj: TTestResult, exp_id: UUID, res_id: UUID) -> "TTestResultDB":
      # This method would be used if TTestResultDB was a separate table being populated
      return TTestResultDB(
          id=res_id,
          experiment_id=exp_id,
          statistic=domain_obj.statistic,
          p_value=domain_obj.p_value,
          degrees_freedom=domain_obj.degrees_freedom,
          confidence_interval_95_lower=domain_obj.confidence_interval_95[0],
          confidence_interval_95_upper=domain_obj.confidence_interval_95[1],
          mean_group_a=domain_obj.mean_group_a,
          mean_group_b=domain_obj.mean_group_b,
          variance_group_a=domain_obj.variance_group_a,
          variance_group_b=domain_obj.variance_group_b,
          is_significant_05=domain_obj.is_significant_05,
          normality_p_value_group_a=domain_obj.normality_p_value_group_a,
          normality_p_value_group_b=domain_obj.normality_p_value_group_b,
          comment=domain_obj.comment
      )


class ExperimentDB(Base): # type: ignore
    """
    SQLAlchemy model for Experiment data.
    """
    __tablename__ = "experiments"

    id = Column(PG_UUID(as_uuid=True), primary_key=True)
    name = Column(String, nullable=True)
    description = Column(String, nullable=True)
    group_a_data = Column(JSON, nullable=False) # List[float]
    group_b_data = Column(JSON, nullable=False) # List[float]
    parameters = Column(JSON, nullable=True)    # Dict[str, Any]

    # Store TTestResult as JSON for simplicity
    # If you need to query on result fields, make TTestResult a separate table
    # or extract key result fields into their own columns here.
    result_statistic = Column(Float, nullable=True)
    result_p_value = Column(Float, nullable=True)
    result_degrees_freedom = Column(Float, nullable=True)
    result_ci_95_lower = Column(Float, nullable=True)
    result_ci_95_upper = Column(Float, nullable=True)
    result_mean_group_a = Column(Float, nullable=True)
    result_mean_group_b = Column(Float, nullable=True)
    result_variance_group_a = Column(Float, nullable=True)
    result_variance_group_b = Column(Float, nullable=True)
    result_is_significant_05 = Column(Boolean, nullable=True)
    result_normality_p_a = Column(Float, nullable=True)
    result_normality_p_b = Column(Float, nullable=True)
    result_comment = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    mlflow_run_id = Column(String, nullable=True)

    def to_domain(self) -> Experiment:
        """Converts this SQLAlchemy model instance to a domain Experiment entity."""
        ttest_result_obj = None
        if self.result_p_value is not None : # Check if result fields are populated
            ttest_result_obj = TTestResult(
                statistic=self.result_statistic,
                p_value=self.result_p_value,
                degrees_freedom=self.result_degrees_freedom,
                confidence_interval_95=(self.result_ci_95_lower, self.result_ci_95_upper),
                mean_group_a=self.result_mean_group_a,
                mean_group_b=self.result_mean_group_b,
                variance_group_a=self.result_variance_group_a,
                variance_group_b=self.result_variance_group_b,
                is_significant_05=self.result_is_significant_05,
                normality_p_value_group_a=self.result_normality_p_a,
                normality_p_value_group_b=self.result_normality_p_b,
                comment=self.result_comment
            )

        return Experiment(
            id=self.id,
            name=self.name,
            description=self.description,
            group_a_data=self.group_a_data, # Assumes JSON decoder returns list
            group_b_data=self.group_b_data, # Assumes JSON decoder returns list
            parameters=self.parameters,     # Assumes JSON decoder returns dict
            result=ttest_result_obj,
            created_at=self.created_at,
            mlflow_run_id=self.mlflow_run_id,
        )

    @staticmethod
    def from_domain(domain_obj: Experiment) -> "ExperimentDB":
        """Converts a domain Experiment entity to an SQLAlchemy model instance."""
        exp_db = ExperimentDB(
            id=domain_obj.id,
            name=domain_obj.name,
            description=domain_obj.description,
            group_a_data=domain_obj.group_a_data,
            group_b_data=domain_obj.group_b_data,
            parameters=domain_obj.parameters,
            created_at=domain_obj.created_at, # Let DB handle default if not set
            mlflow_run_id=domain_obj.mlflow_run_id,
        )
        if domain_obj.result:
            res = domain_obj.result
            exp_db.result_statistic = res.statistic
            exp_db.result_p_value = res.p_value
            exp_db.result_degrees_freedom = res.degrees_freedom
            exp_db.result_ci_95_lower = res.confidence_interval_95[0]
            exp_db.result_ci_95_upper = res.confidence_interval_95[1]
            exp_db.result_mean_group_a = res.mean_group_a
            exp_db.result_mean_group_b = res.mean_group_b
            exp_db.result_variance_group_a = res.variance_group_a
            exp_db.result_variance_group_b = res.variance_group_b
            exp_db.result_is_significant_05 = res.is_significant_05
            exp_db.result_normality_p_a = res.normality_p_value_group_a
            exp_db.result_normality_p_b = res.normality_p_value_group_b
            exp_db.result_comment = res.comment
        return exp_db


# --- SQLAlchemy Repository Implementation ---
class SQLAlchemyStatsRepository(StatsRepository):
    """
    SQLAlchemy implementation of the StatsRepository port.
    Manages persistence of Experiment entities.
    """

    def __init__(self, database_url: str, pool_recycle: int = 3600, pool_pre_ping: bool = True):
        """
        Initializes the repository with a database URL.

        Args:
            database_url: The connection string for the SQLAlchemy database.
                          Example: "postgresql://user:pass@host:port/dbname"
            pool_recycle: Recycles connections after this many seconds.
            pool_pre_ping: Enables "pre-ping" to test connections before use.
        """
        if not database_url:
            raise ValueError("Database URL cannot be empty.")

        self.engine = create_engine(database_url, pool_recycle=pool_recycle, pool_pre_ping=pool_pre_ping)
        self._session_factory = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        # Create tables if they don't exist (useful for dev/testing, use Alembic for prod)
        # Base.metadata.create_all(bind=self.engine) # Moved to init_db.py or Alembic

        logger.info(f"SQLAlchemyStatsRepository initialized with DB URL: {database_url.split('@')[-1] if '@' in database_url else database_url}")


    def _get_session(self) -> SQLAlchemySession:
        """Provides a SQLAlchemy session."""
        return self._session_factory()

    def save(self, experiment: Experiment) -> None:
        """
        Saves an Experiment to the database.
        This is an upsert operation based on the experiment ID.
        """
        logger.debug(f"Attempting to save experiment with ID: {experiment.id}")
        session = self._get_session()
        try:
            # Check if exists
            exp_db_existing = session.query(ExperimentDB).filter(ExperimentDB.id == experiment.id).first()

            if exp_db_existing:
                logger.debug(f"Experiment {experiment.id} found, updating.")
                # Update existing record's fields from domain object
                exp_db_existing.name = experiment.name
                exp_db_existing.description = experiment.description
                exp_db_existing.group_a_data = experiment.group_a_data
                exp_db_existing.group_b_data = experiment.group_b_data
                exp_db_existing.parameters = experiment.parameters
                exp_db_existing.mlflow_run_id = experiment.mlflow_run_id
                # Update result fields
                if experiment.result:
                    res = experiment.result
                    exp_db_existing.result_statistic = res.statistic
                    exp_db_existing.result_p_value = res.p_value
                    exp_db_existing.result_degrees_freedom = res.degrees_freedom
                    exp_db_existing.result_ci_95_lower = res.confidence_interval_95[0]
                    exp_db_existing.result_ci_95_upper = res.confidence_interval_95[1]
                    exp_db_existing.result_mean_group_a = res.mean_group_a
                    exp_db_existing.result_mean_group_b = res.mean_group_b
                    exp_db_existing.result_variance_group_a = res.variance_group_a
                    exp_db_existing.result_variance_group_b = res.variance_group_b
                    exp_db_existing.result_is_significant_05 = res.is_significant_05
                    exp_db_existing.result_normality_p_a = res.normality_p_value_group_a
                    exp_db_existing.result_normality_p_b = res.normality_p_value_group_b
                    exp_db_existing.result_comment = res.comment
                else: # Clear result fields if domain object has no result
                    exp_db_existing.result_statistic = None
                    # ... clear all other result fields ...
                    exp_db_existing.result_comment = None

            else:
                logger.debug(f"Experiment {experiment.id} not found, creating new.")
                exp_db = ExperimentDB.from_domain(experiment)
                session.add(exp_db)

            session.commit()
            logger.info(f"Experiment {experiment.id} saved successfully.")
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving experiment {experiment.id}: {e}", exc_info=True)
            raise
        finally:
            session.close()

    def get_by_id(self, experiment_id: UUID) -> Optional[Experiment]:
        """
        Retrieves an Experiment by its ID.

        Returns:
            The Experiment entity if found, otherwise None.
        """
        logger.debug(f"Attempting to retrieve experiment with ID: {experiment_id}")
        session = self._get_session()
        try:
            exp_db = session.query(ExperimentDB).filter(ExperimentDB.id == experiment_id).first()
            if exp_db:
                logger.info(f"Experiment {experiment_id} retrieved successfully.")
                return exp_db.to_domain()
            logger.info(f"Experiment {experiment_id} not found.")
            return None
        except Exception as e:
            logger.error(f"Error retrieving experiment {experiment_id}: {e}", exc_info=True)
            raise
        finally:
            session.close()

    def list_all(self, limit: int = 100, offset: int = 0) -> List[Experiment]:
        """
        Lists all Experiments with pagination.

        Returns:
            A list of Experiment entities.
        """
        logger.debug(f"Listing all experiments with limit={limit}, offset={offset}")
        session = self._get_session()
        try:
            exp_dbs = session.query(ExperimentDB).order_by(ExperimentDB.created_at.desc()).limit(limit).offset(offset).all()
            domain_experiments = [exp_db.to_domain() for exp_db in exp_dbs]
            logger.info(f"Retrieved {len(domain_experiments)} experiments.")
            return domain_experiments
        except Exception as e:
            logger.error(f"Error listing experiments: {e}", exc_info=True)
            raise
        finally:
            session.close()

# Example usage:
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Replace with your actual database URL
    # For local testing, you might use SQLite: "sqlite:///./test_aletheia_stats.db"
    # Ensure PostgreSQL is running if using "postgresql://..."
    TEST_DB_URL = "sqlite:///./test_aletheia_stats_repo.db"
    import os
    if TEST_DB_URL.startswith("sqlite:") and os.path.exists(TEST_DB_URL.replace("sqlite:///", "")):
        os.remove(TEST_DB_URL.replace("sqlite:///", ""))
        logger.info("Removed old SQLite test database.")

    repo = SQLAlchemyStatsRepository(database_url=TEST_DB_URL)

    # Important: Create tables for SQLite if they don't exist
    # For PostgreSQL, Alembic should handle this.
    Base.metadata.create_all(bind=repo.engine)
    logger.info("Database tables created (if they didn't exist).")

    # Create a sample experiment
    exp_id_1 = UUID("a1a1a1a1-b1b1-c1c1-d1d1-e1e1e1e1e1e1")
    sample_result = TTestResult(
        statistic=1.99, p_value=0.051, degrees_freedom=98,
        confidence_interval_95=( -0.01, 0.99),
        mean_group_a=10.5, mean_group_b=10.0, variance_group_a=2.0, variance_group_b=2.1,
        is_significant_05=False, normality_p_value_group_a=0.6, normality_p_value_group_b=0.7,
        comment="Almost significant."
    )
    experiment1 = Experiment(
        id=exp_id_1,
        name="Test Experiment Alpha",
        description="An experiment to test the repository.",
        group_a_data=[10, 11, 10.5], group_b_data=[9.5, 10, 10.5],
        parameters={"alpha": 0.05},
        result=sample_result,
        mlflow_run_id="mlf_run_alpha"
    )

    logger.info(f"Saving experiment 1 (ID: {exp_id_1})...")
    repo.save(experiment1)

    logger.info(f"Retrieving experiment 1 (ID: {exp_id_1})...")
    retrieved_exp1 = repo.get_by_id(exp_id_1)
    if retrieved_exp1:
        assert retrieved_exp1.id == exp_id_1
        assert retrieved_exp1.name == "Test Experiment Alpha"
        assert retrieved_exp1.result is not None
        assert abs(retrieved_exp1.result.p_value - 0.051) < 1e-6
        logger.info(f"Experiment 1 retrieved and basic assertions passed: {retrieved_exp1.name}")
        logger.info(f"Retrieved result comment: {retrieved_exp1.result.comment}")
    else:
        logger.error("Failed to retrieve experiment 1.")

    # Create and save another experiment
    exp_id_2 = UUID("a2a2a2a2-b2b2-c2c2-d2d2-e2e2e2e2e2e2")
    experiment2 = Experiment(
        id=exp_id_2, name="Test Experiment Beta",
        group_a_data=[1,2,3], group_b_data=[4,5,6] # No result this time
    )
    logger.info(f"Saving experiment 2 (ID: {exp_id_2})...")
    repo.save(experiment2)

    retrieved_exp2 = repo.get_by_id(exp_id_2)
    if retrieved_exp2:
         logger.info(f"Experiment 2 retrieved: {retrieved_exp2.name}. Result should be None: {retrieved_exp2.result is None}")
         assert retrieved_exp2.result is None

    # Update experiment 1
    experiment1_updated_desc = "An experiment to test repository updates."
    experiment1.description = experiment1_updated_desc
    experiment1.result.comment = "Updated comment: Now significant after re-eval!" # type: ignore
    experiment1.result.is_significant_05 = True # type: ignore
    logger.info(f"Updating experiment 1 (ID: {exp_id_1}) with new description and result comment...")
    repo.save(experiment1) # This should perform an update

    retrieved_exp1_updated = repo.get_by_id(exp_id_1)
    if retrieved_exp1_updated:
        assert retrieved_exp1_updated.description == experiment1_updated_desc
        assert retrieved_exp1_updated.result is not None
        assert retrieved_exp1_updated.result.comment == "Updated comment: Now significant after re-eval!"
        assert retrieved_exp1_updated.result.is_significant_05 is True
        logger.info(f"Experiment 1 updated and assertions passed. New comment: {retrieved_exp1_updated.result.comment}")
    else:
        logger.error("Failed to retrieve updated experiment 1.")


    logger.info("Listing all experiments...")
    all_experiments = repo.list_all()
    assert len(all_experiments) >= 2
    logger.info(f"Found {len(all_experiments)} experiments:")
    for exp in all_experiments:
        logger.info(f"  - ID: {exp.id}, Name: {exp.name}, Created: {exp.created_at}, MLflow ID: {exp.mlflow_run_id}")
        if exp.result:
            logger.info(f"    Result p-value: {exp.result.p_value}, Comment: {exp.result.comment}")

    logger.info("SQLAlchemyStatsRepository test completed.")
    # Clean up the test SQLite database file
    if TEST_DB_URL.startswith("sqlite:") and os.path.exists(TEST_DB_URL.replace("sqlite:///", "")):
        os.remove(TEST_DB_URL.replace("sqlite:///", ""))
        logger.info("Cleaned up SQLite test database.")
