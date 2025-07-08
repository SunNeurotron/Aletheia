# Aletheia_v3/tests/core/mdl_synthesis/test_adapters.py
import unittest
import pickle
import uuid

# Import the function to test
from Aletheia_v3.core.mdl_synthesis.adapters import map_concept_to_representation, deserialize_model_representation_content
# Import the necessary domain models
from Aletheia_v3.core.domain_models import ScientificConcept, ConceptType
from Aletheia_v3.core.mdl_synthesis.entities import ModelRepresentation

class TestAdapters(unittest.TestCase):

    def test_map_concept_to_representation_and_deserialize(self):
        # 1. Create a sample ScientificConcept
        concept_id = uuid.uuid4()
        sample_concept = ScientificConcept(
            id=concept_id,
            name="Test Cluster Alpha",
            description="A sample cluster for testing MDL adapter.",
            concept_type=ConceptType.CLUSTER,
            properties={
                "member_ucm_ids": ["ucm1", "ucm2", "ucm3"],
                "shared_keywords": ["test", "mdl", "cluster"],
                "embedding": [0.1, 0.2, 0.3] # Example embedding
            },
            # created_at and updated_at will have default values
        )

        # 2. Call the adapter
        model_repr = map_concept_to_representation(sample_concept)

        # 3. Verify the ModelRepresentation output
        self.assertIsInstance(model_repr, ModelRepresentation)
        self.assertEqual(model_repr.identifier, str(concept_id))
        self.assertIsInstance(model_repr.content, bytes)

        # 4. Deserialize the content and verify its structure and values
        deserialized_content = deserialize_model_representation_content(model_repr)

        self.assertIsInstance(deserialized_content, dict)
        self.assertEqual(deserialized_content.get("id"), str(concept_id))
        self.assertEqual(deserialized_content.get("name"), "Test Cluster Alpha")
        self.assertEqual(deserialized_content.get("description"), "A sample cluster for testing MDL adapter.")
        self.assertEqual(deserialized_content.get("concept_type"), ConceptType.CLUSTER.value)

        properties = deserialized_content.get("properties")
        self.assertIsInstance(properties, dict)
        self.assertEqual(properties.get("member_ucm_ids"), ["ucm1", "ucm2", "ucm3"])
        self.assertEqual(properties.get("shared_keywords"), ["test", "mdl", "cluster"])
        self.assertEqual(properties.get("embedding"), [0.1, 0.2, 0.3])

    def test_map_concept_with_minimal_data(self):
        concept_id = uuid.uuid4()
        sample_concept = ScientificConcept(
            id=concept_id,
            name="Minimal Concept",
            concept_type=ConceptType.UCM
            # No description, minimal properties
        )
        model_repr = map_concept_to_representation(sample_concept)
        self.assertEqual(model_repr.identifier, str(concept_id))

        deserialized_content = deserialize_model_representation_content(model_repr)
        self.assertEqual(deserialized_content.get("name"), "Minimal Concept")
        self.assertIsNone(deserialized_content.get("description")) # Or check against ScientificConcept's default
        self.assertEqual(deserialized_content.get("concept_type"), ConceptType.UCM.value)
        self.assertEqual(deserialized_content.get("properties"), {}) # Default from ScientificConcept

if __name__ == '__main__':
    unittest.main()
