from typing import List, Dict
import networkx as nx # For type hinting, though actual use is in _identify_patterns
from datetime import datetime # For UnifiedTheory ID generation
import hashlib # For UnifiedTheory ID generation

# Assuming domain_models are in the same package or accessible
# For now, relative import, adjust if structure differs or use absolute path from project root
from .domain_models import ConceptCluster, Pattern, UnifiedTheory, ConceptualUnit # Added ConceptualUnit here for DomainService

class TheoryBuilder:
    """Servicio de dominio para construcción de teorías"""
    def synthesize_theory(
        self,
        clusters: List[ConceptCluster]
    ) -> UnifiedTheory:
        """Sintetiza teoría unificada desde clusters"""
        patterns = self._identify_patterns(clusters)
        principles = self._extract_principles(patterns)
        formal_relations = self._formalize_relations(clusters)
        validation_metrics = self._validate_theory(principles, patterns) # Pasar patterns aquí

        return UnifiedTheory(
            id=f"theory_{hashlib.sha1(str(datetime.now()).encode()).hexdigest()[:8]}",
            patterns=patterns,
            principles=principles,
            relations=formal_relations,
            validation_metrics=validation_metrics
        )

    def _identify_patterns(self, clusters: List[ConceptCluster]) -> List[Pattern]:
        """
        Identifica patrones estructurales simples (Path y Star) en los grafos de los ConceptCluster.

        Args:
            clusters: Una lista de ConceptCluster, cada uno potencialmente con un grafo.

        Returns:
            Una lista de objetos Pattern representando los patrones identificados.
        """
        identified_patterns: List[Pattern] = []
        if not clusters:
            return identified_patterns

        for i, cluster in enumerate(clusters):
            if not cluster.graph or cluster.graph.number_of_nodes() == 0:
                continue

            G = cluster.graph
            num_nodes = G.number_of_nodes()

            # Intentar identificar Path Graph
            if nx.is_connected(G):
                degrees = [d for n, d in G.degree()]
                is_path_like = num_nodes >= 2 and degrees.count(1) == 2 and degrees.count(2) == num_nodes - 2
                is_tree = nx.is_tree(G) # Un path es un tipo de árbol

                if is_path_like and is_tree:
                    pattern_id = f"pattern_path_{cluster.units[0].id if cluster.units else i}"
                    elements_involved = list(G.nodes()) # IDs de ConceptualUnit
                    identified_patterns.append(
                        Pattern(id=pattern_id, description=f"Path structure identified in cluster starting with {elements_involved[0] if elements_involved else 'unknown'}", elements=elements_involved)
                    )
                    continue # Si es path, no puede ser estrella (para >2 nodos)

                # Intentar identificar Star Graph (si no es un path)
                if num_nodes >= 3:
                    central_nodes = [n for n, d in G.degree() if d == num_nodes - 1]
                    leaf_nodes = [n for n, d in G.degree() if d == 1]

                    if len(central_nodes) == 1 and len(leaf_nodes) == num_nodes - 1:
                        center_node_id = central_nodes[0]
                        # Verificar que todas las hojas estén conectadas al centro
                        # y que el grafo sea un árbol (una estrella es un árbol).
                        is_star_candidate = True
                        for leaf_node_id in leaf_nodes:
                            if not G.has_edge(center_node_id, leaf_node_id):
                                is_star_candidate = False
                                break
                        if is_star_candidate and nx.is_tree(G):
                            pattern_id = f"pattern_star_{cluster.units[0].id if cluster.units else i}"
                            elements_involved = list(G.nodes()) # IDs de ConceptualUnit
                            identified_patterns.append(
                                Pattern(id=pattern_id, description=f"Star structure identified with center {center_node_id}", elements=elements_involved)
                            )
        return identified_patterns

    def _extract_principles(self, patterns: List[Pattern]) -> List[str]:
        """
        Extrae principios descriptivos basados en los patrones identificados.

        Args:
            patterns: Una lista de objetos Pattern.

        Returns:
            Una lista de strings, donde cada string es un principio.
        """
        principles: List[str] = []
        if not patterns:
            return principles

        for pattern in patterns:
            if "path" in pattern.id.lower():
                principles.append(f"Principle of Linear Progression/Causality (derived from {pattern.description})")
            elif "star" in pattern.id.lower():
                principles.append(f"Principle of Centralized Influence/Convergence (derived from {pattern.description})")
            else:
                principles.append(f"General Structural Principle (derived from {pattern.description})")
        return principles

    def _formalize_relations(self, clusters: List[ConceptCluster]) -> Dict[str, List[str]]:
        """
        Formaliza las relaciones dentro de cada clúster.

        Para cada clúster, toma el ID de la primera unidad conceptual como clave
        y una lista de los IDs de las unidades restantes como valor.

        Args:
            clusters: Una lista de ConceptCluster.

        Returns:
            Un diccionario representando las relaciones formalizadas.
        """
        relations: Dict[str, List[str]] = {}
        if not clusters:
            return relations

        for cluster in clusters:
            if cluster.units and len(cluster.units) > 0:
                key_concept_id = cluster.units[0].id
                related_concept_ids = [unit.id for unit in cluster.units[1:]]

                if related_concept_ids:
                    relations[key_concept_id] = related_concept_ids
        return relations

    def _validate_theory(self, principles: List[str], patterns: List[Pattern]) -> Dict[str, float]:
        """
        Calcula métricas de validación para una teoría basada en sus principios y patrones.

        Args:
            principles: Lista de principios de la teoría.
            patterns: Lista de patrones identificados en la teoría.

        Returns:
            Un diccionario con métricas de validación, como 'consistency_score'.
        """
        num_principles = len(principles)
        num_patterns = len(patterns)
        consistency = 0.0

        if num_principles > 0 and num_patterns > 0:
            # Asumimos que cada principio generado por _extract_principles se basa en un patrón.
            consistency = 1.0
        elif num_principles == 0 and num_patterns == 0:
            consistency = 1.0 # Vacuamente consistente.

        validation_metrics = {
            "consistency_score": consistency,
            "num_derived_principles": float(num_principles),
            "num_identified_patterns": float(num_patterns)
        }
        return validation_metrics

# Note: The original mdu_cube_system.py also had a DomainService class.
# That class was more of an application service as it orchestrated calls to TheoryBuilder
# and other conceptual domain methods (extract_atomic_units, form_clusters etc.)
# For true domain services, they should encapsulate domain logic.
# TheoryBuilder fits well here. If DomainService from mdu_cube_system.py is purely domain logic,
# it could also reside here or its methods be part of other domain services.
# For now, only TheoryBuilder is moved as per the plan.
# The existing Aletheia_v3/core/domain.py or use_cases.py might already have a DomainService.
# This needs to be checked to avoid conflicts and ensure proper layering.
# The plan specifies AnalysisUseCase and CubicAnalysisPipeline (which uses DomainService)
# go into application/use_cases.py. So the DomainService in mdu_cube_system.py
# seems to be the one that Application layer's use cases will depend on.
# It acts as a facade to the more granular domain elements like TheoryBuilder.
#
# Let's include the DomainService from mdu_cube_system.py here as it directly uses TheoryBuilder
# and its methods (extract_atomic_units, etc.) are domain-focused operations.

import numpy as np # For ConceptualUnit embeddings in DomainService placeholders
import uuid # Para IDs únicos
# from .domain_models import ConceptualUnit, ConceptCluster, UnifiedTheory # Relative import - Now covered by the top import

class DomainService: # This was in mdu_cube_system.py, fits here as it uses TheoryBuilder
    def __init__(self, theory_builder: TheoryBuilder):
        self.theory_builder = theory_builder

    async def extract_atomic_units(self, session_data: str) -> List[ConceptualUnit]:
        # print(f"DomainService: Extracting atomic units from data of length {len(session_data)}") # Placeholder
        # Placeholder: Create some dummy conceptual units
        return [
            ConceptualUnit(id="ds_unit1", content="First concept from DS", embeddings=np.random.rand(10), relations={"ds_unit2"}, metadata={"source":"docA_ds"}),
            ConceptualUnit(id="ds_unit2", content="Second concept from DS", embeddings=np.random.rand(10), relations={"ds_unit1"}, metadata={"source":"docB_ds"})
        ]

    async def form_clusters(self, atoms: List[ConceptualUnit]) -> List[ConceptCluster]:
        # print(f"DomainService: Forming clusters from {len(atoms)} atomic units.") # Placeholder
        if not atoms: return []
        # Placeholder: Simple clustering
        return [ConceptCluster(atoms)] if atoms else []

    async def build_mini_theories(self, clusters: List[ConceptCluster]) -> List[UnifiedTheory]:
        """
        Construye una lista de "mini-teorías", una para cada clúster de conceptos.

        Utiliza el TheoryBuilder para sintetizar una UnifiedTheory para cada clúster.
        El ID de cada mini-teoría es generado por el TheoryBuilder.

        Args:
            clusters: Una lista de ConceptCluster.

        Returns:
            Una lista de objetos UnifiedTheory, cada uno representando una mini-teoría.
        """
        # print(f"DomainService: Building mini-theories from {len(clusters)} clusters.") # Placeholder
        if not clusters:
            return []
        mini_theories = []
        for cluster in clusters: # No need for index 'i' if not used for ID
            # ID de la teoría ya es asignado unívocamente por self.theory_builder.synthesize_theory
            theory = self.theory_builder.synthesize_theory([cluster])
            mini_theories.append(theory)
        return mini_theories

    async def synthesize_model(self, theories: List[UnifiedTheory]) -> UnifiedTheory:
        """
        Sintetiza un modelo unificado a partir de una lista de mini-teorías.

        El modelo unificado agrega los patrones, principios y relaciones de todas
        las mini-teorías de entrada. Los principios se hacen únicos. Las relaciones
        se fusionan, y las listas de conceptos relacionados para una misma clave
        también se hacen únicas. Las métricas de validación numéricas se promedian.
        Se genera un nuevo ID único para el modelo unificado.

        Args:
            theories: Una lista de UnifiedTheory (mini-teorías).

        Returns:
            Un único objeto UnifiedTheory que representa el modelo agregado.
        """
        # print(f"DomainService: Synthesizing unified model from {len(theories)} mini-theories.") # Placeholder

        unified_model_id = f"unified_model_{uuid.uuid4().hex[:8]}"

        if not theories:
            return UnifiedTheory(id=unified_model_id, patterns=[], principles=[], relations={}, validation_metrics={})

        all_patterns: List[Pattern] = []
        all_principles_set: set[str] = set()
        all_relations: Dict[str, List[str]] = {}

        summed_metrics: Dict[str, float] = {}
        metric_counts: Dict[str, int] = {}

        for theory in theories:
            all_patterns.extend(theory.patterns)
            for principle in theory.principles:
                all_principles_set.add(principle)

            for key, value_list in theory.relations.items():
                if key not in all_relations:
                    all_relations[key] = []
                # Evitar duplicados dentro de la lista de relaciones para una misma clave
                for item in value_list:
                    if item not in all_relations[key]:
                        all_relations[key].append(item)

            for metric_key, metric_value in theory.validation_metrics.items():
                if isinstance(metric_value, (int, float)): # Solo promediar numéricos
                    summed_metrics[metric_key] = summed_metrics.get(metric_key, 0.0) + metric_value
                    metric_counts[metric_key] = metric_counts.get(metric_key, 0) + 1

        averaged_metrics: Dict[str, float] = {}
        for key, total_sum in summed_metrics.items():
            count = metric_counts.get(key, 0)
            if count > 0:
                averaged_metrics[key] = total_sum / count

        # Por ahora, simple concatenación de patrones. La unicidad de patrones podría manejarse
        # si Pattern.id fuera un identificador único fiable para la deduplicación.
        final_patterns = all_patterns
        final_principles = list(all_principles_set)

        unified_model = UnifiedTheory(
            id=unified_model_id,
            patterns=final_patterns,
            principles=final_principles,
            relations=all_relations,
            validation_metrics=averaged_metrics
        )
        return unified_model

    def calculate_metrics(self, unified_model: UnifiedTheory) -> Dict[str, float]:
        """
        Calcula métricas adicionales para un modelo unificado.

        Estas métricas son sobre la estructura general del modelo unificado,
        como el número total de patrones, principios y claves de relación.
        Se combinan con las `validation_metrics` existentes en el modelo
        (que, si el modelo fue sintetizado, representan promedios de mini-teorías).

        Args:
            unified_model: El objeto UnifiedTheory para el cual calcular métricas.

        Returns:
            Un diccionario de métricas combinadas.
        """
        # print(f"DomainService: Calculating metrics for model {unified_model.id}") # Placeholder

        calculated_overall_metrics = {
            "overall_num_patterns": float(len(unified_model.patterns)),
            "overall_num_principles": float(len(unified_model.principles)),
            "overall_num_relation_keys": float(len(unified_model.relations)),
        }
        # Combinar con las métricas de validación ya existentes en el modelo.
        # Las claves en calculated_overall_metrics podrían sobrescribir las de validation_metrics
        # si hay colisión, aunque aquí se nombran para ser distintas ('overall_').
        final_metrics = {**unified_model.validation_metrics, **calculated_overall_metrics}
        return final_metrics
# Este fragmento final de "**unified_model.validation_metrics" estaba duplicado y causaba error de sintaxis.
# Lo he eliminado de la segunda posición. La fusión correcta es la que está en final_metrics.
