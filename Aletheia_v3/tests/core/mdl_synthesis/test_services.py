# Aletheia_v3/tests/core/mdl_synthesis/test_services.py
import unittest
import gzip
import pickle
import logging
from unittest.mock import patch, MagicMock

# Import services to test
from Aletheia_v3.core.mdl_synthesis.services import (
    KolmogorovComplexityProxyService,
    LikelihoodService,
    OmegaCostService
)
# Import entities needed for tests
from Aletheia_v3.core.mdl_synthesis.entities import ModelRepresentation

class TestMDLServices(unittest.TestCase):

    def setUp(self):
        self.complexity_service = KolmogorovComplexityProxyService()
        self.omega_cost_service = OmegaCostService()
        self.likelihood_service = LikelihoodService() # Placeholder service

    def test_kolmogorov_complexity_proxy_service(self):
        # Test with some simple content
        model_obj = {"param1": "value1", "param2": [1, 2, 3]}
        model_content_bytes = pickle.dumps(model_obj)

        complexity = self.complexity_service.compute(model_content_bytes)
        self.assertIsInstance(complexity, float)
        self.assertGreaterEqual(complexity, 0)

        # Expected length of gzipped pickled content
        expected_complexity = float(len(gzip.compress(model_content_bytes)))
        self.assertEqual(complexity, expected_complexity)

        # Test with empty content
        empty_complexity = self.complexity_service.compute(b"")
        self.assertEqual(empty_complexity, 0.0)

    def test_omega_cost_service(self):
        complexity = 50.0
        log_likelihood = -15.0
        lambda_param = 1.0

        mdl_cost = self.omega_cost_service.calculate_mdl_cost(complexity, log_likelihood, lambda_param)
        # Expected: Cost(M) = λ * K(M) - L(D|M) = 1.0 * 50.0 - (-15.0) = 50.0 + 15.0 = 65.0
        self.assertEqual(mdl_cost, 65.0)

        lambda_param_zero = 0.0
        mdl_cost_lambda_zero = self.omega_cost_service.calculate_mdl_cost(complexity, log_likelihood, lambda_param_zero)
        # Expected: 0.0 * 50.0 - (-15.0) = 15.0
        self.assertEqual(mdl_cost_lambda_zero, 15.0)

        # Test with negative lambda (should raise ValueError)
        with self.assertRaises(ValueError):
            self.omega_cost_service.calculate_mdl_cost(complexity, log_likelihood, -0.5)

    def test_likelihood_service_placeholder(self):
        # Create a dummy ModelRepresentation and data
        # The content of these doesn't matter for the placeholder
        dummy_model_repr = ModelRepresentation(identifier="test_model", content=b"dummy_content")
        dummy_data = {"x": [1,2], "y": [3,4]}

        # Mock the logger used within LikelihoodService
        # The logger is obtained by logging.getLogger(__name__) where __name__ is the module name.
        # So, we need to patch 'Aletheia_v3.core.mdl_synthesis.services.logger.warning'
        with patch('Aletheia_v3.core.mdl_synthesis.services.logger.warning') as mock_log_warning:
            likelihood_value = self.likelihood_service.compute(dummy_model_repr, dummy_data)

            # Verify it returns a float
            self.assertIsInstance(likelihood_value, float)
            # Verify it's within the specified random range for the placeholder
            self.assertTrue(-50.0 <= likelihood_value <= -1.0) # Adjusted based on service impl.

            # Verify that the warning was logged
            mock_log_warning.assert_called_once()
            # Check if the log message contains the expected text
            args, _ = mock_log_warning.call_args
            self.assertIn("LikelihoodService.compute no está implementado con lógica real.", args[0])


if __name__ == '__main__':
    unittest.main()
