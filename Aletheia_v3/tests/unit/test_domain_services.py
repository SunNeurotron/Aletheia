import pytest
from unittest.mock import MagicMock, patch
import networkx as nx
import uuid

from Aletheia_v3.core.domain_services import TheoryBuilder, DomainService
from Aletheia_v3.core.domain_models import ConceptCluster, ConceptualUnit, Pattern, UnifiedTheory

# --- Fixtures ---

@pytest.fixture
def theory_builder_instance():
    """Returns a TheoryBuilder instance."""
    return TheoryBuilder()

@pytest.fixture
def mock_theory_builder():
    """Returns a MagicMock for TheoryBuilder."""
    return MagicMock(spec=TheoryBuilder)

@pytest.fixture
def domain_service_instance(mock_theory_builder):
    """Returns a DomainService instance with a mocked TheoryBuilder."""
    return DomainService(theory_builder=mock_theory_builder)

# --- Helper Functions for Creating Test Data ---

def create_conceptual_unit(id_suffix: str, content: str = "content") -> ConceptualUnit:
    return ConceptualUnit(id=f"unit_{id_suffix}", content=content, embeddings=MagicMock(), relations=set(), metadata={})

def create_concept_cluster(units: List[ConceptualUnit], graph: nx.Graph = None) -> ConceptCluster:
    cluster = ConceptCluster(units=units)
    if graph:
        cluster.graph = graph
    else: # Crear un grafo simple si no se provee
        g = nx.Graph()
        if units:
            for unit in units:
                g.add_node(unit.id) # Asumimos que el ID de la unidad es el nodo del grafo
            if len(units) > 1:
                for i in range(len(units) - 1):
                    g.add_edge(units[i].id, units[i+1].id)
        cluster.graph = g
    return cluster

# --- Tests for TheoryBuilder ---

class TestTheoryBuilder:

    def test_identify_patterns_empty(self, theory_builder_instance: TheoryBuilder):
        assert theory_builder_instance._identify_patterns([]) == []
        cluster_no_graph = MagicMock(spec=ConceptCluster)
        cluster_no_graph.graph = None
        assert theory_builder_instance._identify_patterns([cluster_no_graph]) == []

        cluster_empty_graph = MagicMock(spec=ConceptCluster)
        empty_g = nx.Graph()
        cluster_empty_graph.graph = empty_g
        assert theory_builder_instance._identify_patterns([cluster_empty_graph]) == []

    def test_identify_patterns_path(self, theory_builder_instance: TheoryBuilder):
        u1, u2, u3 = create_conceptual_unit("p1"), create_conceptual_unit("p2"), create_conceptual_unit("p3")
        path_graph = nx.Graph()
        path_graph.add_nodes_from([u1.id, u2.id, u3.id])
        path_graph.add_edges_from([(u1.id, u2.id), (u2.id, u3.id)])
        cluster = create_concept_cluster(units=[u1, u2, u3], graph=path_graph)

        patterns = theory_builder_instance._identify_patterns([cluster])
        assert len(patterns) == 1
        assert "path" in patterns[0].id.lower()
        assert patterns[0].description.startswith("Path structure identified")
        assert set(patterns[0].elements) == {u1.id, u2.id, u3.id}

    def test_identify_patterns_star(self, theory_builder_instance: TheoryBuilder):
        center = create_conceptual_unit("center")
        l1, l2, l3 = create_conceptual_unit("l1"), create_conceptual_unit("l2"), create_conceptual_unit("l3")
        star_graph = nx.Graph()
        star_graph.add_nodes_from([center.id, l1.id, l2.id, l3.id])
        star_graph.add_edges_from([(center.id, l1.id), (center.id, l2.id), (center.id, l3.id)])
        cluster = create_concept_cluster(units=[center, l1, l2, l3], graph=star_graph)

        patterns = theory_builder_instance._identify_patterns([cluster])
        assert len(patterns) == 1
        assert "star" in patterns[0].id.lower()
        assert f"center {center.id}" in patterns[0].description
        assert set(patterns[0].elements) == {center.id, l1.id, l2.id, l3.id}

    def test_identify_patterns_no_specific_pattern(self, theory_builder_instance: TheoryBuilder):
        # Grafo que no es ni path ni estrella simple (e.g., un ciclo o un grafo más denso)
        u1, u2, u3, u4 = create_conceptual_unit("c1"), create_conceptual_unit("c2"), create_conceptual_unit("c3"), create_conceptual_unit("c4")
        cycle_graph = nx.Graph()
        cycle_graph.add_nodes_from([u1.id, u2.id, u3.id, u4.id])
        cycle_graph.add_edges_from([(u1.id, u2.id), (u2.id, u3.id), (u3.id, u4.id), (u4.id, u1.id)]) # Ciclo de 4
        cluster = create_concept_cluster(units=[u1,u2,u3,u4], graph=cycle_graph)

        patterns = theory_builder_instance._identify_patterns([cluster])
        assert len(patterns) == 0 # La lógica actual solo identifica paths y estrellas


    def test_extract_principles(self, theory_builder_instance: TheoryBuilder):
        path_pattern = Pattern(id="pattern_path_test", description="Path test desc", elements=[])
        star_pattern = Pattern(id="pattern_star_test", description="Star test desc", elements=[])
        other_pattern = Pattern(id="pattern_other_test", description="Other test desc", elements=[])

        principles = theory_builder_instance._extract_principles([path_pattern, star_pattern, other_pattern])
        assert len(principles) == 3
        assert "Principle of Linear Progression/Causality (derived from Path test desc)" in principles
        assert "Principle of Centralized Influence/Convergence (derived from Star test desc)" in principles
        assert "General Structural Principle (derived from Other test desc)" in principles

        assert theory_builder_instance._extract_principles([]) == []

    def test_formalize_relations(self, theory_builder_instance: TheoryBuilder):
        u1, u2, u3 = create_conceptual_unit("r1"), create_conceptual_unit("r2"), create_conceptual_unit("r3")
        cluster1 = create_concept_cluster(units=[u1, u2, u3]) # Grafo por defecto se crea

        u4 = create_conceptual_unit("r4")
        cluster2 = create_concept_cluster(units=[u4]) # Un solo nodo

        cluster3 = create_concept_cluster(units=[]) # Vacío

        relations = theory_builder_instance._formalize_relations([cluster1, cluster2, cluster3])

        assert u1.id in relations
        assert set(relations[u1.id]) == {u2.id, u3.id}
        assert u4.id not in relations # No hay otros conceptos para relacionar
        assert len(relations) == 1

        assert theory_builder_instance._formalize_relations([]) == {}


    def test_validate_theory(self, theory_builder_instance: TheoryBuilder):
        patterns = [Pattern(id="p1", description="d1", elements=[])]
        principles = ["principle from p1"]
        metrics = theory_builder_instance._validate_theory(principles, patterns)
        assert metrics["consistency_score"] == 1.0
        assert metrics["num_derived_principles"] == 1.0
        assert metrics["num_identified_patterns"] == 1.0

        metrics_no_patterns = theory_builder_instance._validate_theory(principles, [])
        assert metrics_no_patterns["consistency_score"] == 0.0 # No hay patrones para apoyar los principios

        metrics_no_principles = theory_builder_instance._validate_theory([], patterns)
        assert metrics_no_principles["consistency_score"] == 0.0 # No hay principios para ser consistentes

        metrics_empty_all = theory_builder_instance._validate_theory([], [])
        assert metrics_empty_all["consistency_score"] == 1.0 # Vacuamente consistente


# --- Tests for DomainService ---

class TestDomainService:

    @pytest.mark.asyncio
    async def test_build_mini_theories_ids(self, domain_service_instance: DomainService, mock_theory_builder: MagicMock):
        # Asegurar que synthesize_theory devuelve un ID único cada vez
        # Esto ya lo hace el TheoryBuilder real usando hash(datetime)
        # Aquí podemos simularlo o confiar en la implementación real si no se mockea profundamente.

        mock_theory_output1 = UnifiedTheory(id="theory_abc", patterns=[], principles=[], relations={}, validation_metrics={})
        mock_theory_output2 = UnifiedTheory(id="theory_def", patterns=[], principles=[], relations={}, validation_metrics={})

        # Si TheoryBuilder.synthesize_theory es mockeado, necesitamos controlar su side_effect
        mock_theory_builder.synthesize_theory.side_effect = [mock_theory_output1, mock_theory_output2]

        u1, u2 = create_conceptual_unit("c1"), create_conceptual_unit("c2")
        cluster1 = create_concept_cluster(units=[u1])
        cluster2 = create_concept_cluster(units=[u2])

        mini_theories = await domain_service_instance.build_mini_theories([cluster1, cluster2])

        assert len(mini_theories) == 2
        # Verifica que los IDs son los que el mock_theory_builder.synthesize_theory devolvió
        assert mini_theories[0].id == "theory_abc"
        assert mini_theories[1].id == "theory_def"
        # O, para mayor robustez, que los IDs son diferentes
        assert mini_theories[0].id != mini_theories[1].id


    @pytest.mark.asyncio
    async def test_synthesize_model_empty_theories(self, domain_service_instance: DomainService):
        result = await domain_service_instance.synthesize_model([])
        assert isinstance(result, UnifiedTheory)
        assert len(result.patterns) == 0
        assert len(result.principles) == 0
        assert len(result.relations) == 0
        assert len(result.validation_metrics) == 0
        assert result.id.startswith("unified_model_")

    @pytest.mark.asyncio
    async def test_synthesize_model_aggregation(self, domain_service_instance: DomainService):
        t1_patterns = [Pattern(id="p1", description="d1", elements=["e1"])]
        t1_principles = ["prin1", "common_prin"]
        t1_relations = {"unit_a": ["unit_b"], "common_key": ["rel1"]}
        t1_metrics = {"metric1": 1.0, "common_metric": 0.5, "metric_str": "info"} # metric_str no se promediará

        t2_patterns = [Pattern(id="p2", description="d2", elements=["e2"]), Pattern(id="p3", description="d3", elements=["e3"])]
        t2_principles = ["prin2", "common_prin"]
        t2_relations = {"unit_c": ["unit_d"], "common_key": ["rel2"]}
        t2_metrics = {"metric1": 0.8, "common_metric": 0.7, "metric2": 0.9}

        theory1 = UnifiedTheory(id="t1", patterns=t1_patterns, principles=t1_principles, relations=t1_relations, validation_metrics=t1_metrics)
        theory2 = UnifiedTheory(id="t2", patterns=t2_patterns, principles=t2_principles, relations=t2_relations, validation_metrics=t2_metrics)

        result = await domain_service_instance.synthesize_model([theory1, theory2])

        assert result.id.startswith("unified_model_")

        # Patterns: concatenación simple
        assert len(result.patterns) == 3
        assert result.patterns[0].id == "p1"
        assert result.patterns[1].id == "p2"
        assert result.patterns[2].id == "p3"

        # Principles: concatenación con unicidad
        assert len(result.principles) == 3
        assert "prin1" in result.principles
        assert "prin2" in result.principles
        assert "common_prin" in result.principles

        # Relations: fusión, listas de valores concatenadas y únicas
        assert len(result.relations) == 3
        assert "unit_a" in result.relations and result.relations["unit_a"] == ["unit_b"]
        assert "unit_c" in result.relations and result.relations["unit_c"] == ["unit_d"]
        assert "common_key" in result.relations and set(result.relations["common_key"]) == {"rel1", "rel2"}

        # Validation Metrics: promedio de las numéricas
        assert len(result.validation_metrics) == 3 # metric1, common_metric, metric2 (metric_str ignorada)
        assert result.validation_metrics["metric1"] == pytest.approx((1.0 + 0.8) / 2)
        assert result.validation_metrics["common_metric"] == pytest.approx((0.5 + 0.7) / 2)
        assert result.validation_metrics["metric2"] == pytest.approx(0.9 / 1) # Solo en t2

    @pytest.mark.asyncio
    async def test_synthesize_model_single_theory(self, domain_service_instance: DomainService):
        # Similar a aggregation pero con una sola teoría
        t1_patterns = [Pattern(id="p_single", description="d_single", elements=["e_s"])]
        t1_principles = ["prin_single"]
        t1_relations = {"unit_s": ["unit_s_rel"]}
        t1_metrics = {"metric_s": 0.77}
        theory1 = UnifiedTheory(id="t_single", patterns=t1_patterns, principles=t1_principles, relations=t1_relations, validation_metrics=t1_metrics)

        result = await domain_service_instance.synthesize_model([theory1])

        assert result.id.startswith("unified_model_")
        assert result.patterns == t1_patterns
        assert result.principles == t1_principles
        assert result.relations == t1_relations
        assert result.validation_metrics == t1_metrics


    def test_calculate_metrics(self, domain_service_instance: DomainService):
        model_metrics = {"consistency_score": 0.8, "num_patterns": 5.0} # Estas serían las promediadas
        model = UnifiedTheory(
            id="test_model",
            patterns=[MagicMock() for _ in range(3)], # 3 patrones
            principles=["p1", "p2"], # 2 principios
            relations={"k1": ["v1"], "k2": ["v2", "v3"]}, # 2 claves de relación
            validation_metrics=model_metrics.copy()
        )

        calculated = domain_service_instance.calculate_metrics(model)

        assert calculated["overall_num_patterns"] == 3.0
        assert calculated["overall_num_principles"] == 2.0
        assert calculated["overall_num_relation_keys"] == 2.0
        # Asegurar que las métricas originales de validation_metrics se conservan
        # y se combinan con las nuevas 'overall'
        assert calculated["consistency_score"] == 0.8
        # assert calculated["num_patterns"] == 5.0 # Esta clave no debería estar si no está en model_metrics

        # Verificar que todas las claves de model_metrics están en calculated
        for k,v in model_metrics.items():
            assert calculated[k] == v

        # Verificar que las claves 'overall' están presentes
        assert "overall_num_patterns" in calculated
        assert "overall_num_principles" in calculated
        assert "overall_num_relation_keys" in calculated
```
