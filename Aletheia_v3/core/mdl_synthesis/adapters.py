# Aletheia_v3/core/mdl_synthesis/adapters.py
import pickle
from typing import Optional # Added Optional for type hinting if needed in future

# Import ModelRepresentation from local entities
from .entities import ModelRepresentation
# Import ScientificConcept from its location in Aletheia_v3.core
# Assuming Aletheia_v3 is in PYTHONPATH or relative imports work from this structure
from ...core.domain_models import ScientificConcept, ConceptType

def map_concept_to_representation(concept: ScientificConcept) -> ModelRepresentation:
    """
    Converts an Aletheia_v3 ScientificConcept into a ModelRepresentation
    suitable for the MDL optimization engine.
    """

    model_content_dict = {
        "id": str(concept.id), # Ensure string representation if id is UUID
        "name": concept.name,
        "description": concept.description,
        # Ensure concept_type.value is used if concept_type is an Enum
        "concept_type": concept.concept_type.value if isinstance(concept.concept_type, ConceptType) else str(concept.concept_type),
        "properties": concept.properties,
        # Consider adding embeddings if they are directly on the concept or in properties
        # "embedding": concept.embedding_vector if hasattr(concept, 'embedding_vector') else None
    }

    # Serialize this dictionary to bytes using pickle
    serialized_content: bytes = pickle.dumps(model_content_dict)

    representation_identifier = str(concept.id)

    return ModelRepresentation(
        identifier=representation_identifier,
        content=serialized_content
    )

# Example of a reverse function (conceptual, may not be needed for MDL optimization itself, for testing)
def deserialize_model_representation_content(representation: ModelRepresentation) -> dict:
    """Deserializes the content of ModelRepresentation back to a dictionary."""
    if representation.content:
        return pickle.loads(representation.content)
    return {}
