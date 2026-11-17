import os
import unittest
from unittest.mock import patch

from utils.provider_config import (
    get_base_url, get_provider, is_local_provider,
    is_openai_compatible, validate_provider_config,
)


class ProviderConfigTests(unittest.TestCase):
    def test_local_models_are_disabled(self):
        with patch.dict(os.environ, {"SHZ_LLM_PROVIDER": "ollama"}, clear=True):
            self.assertEqual(get_provider(), "ollama")
            self.assertTrue(is_local_provider())
            self.assertFalse(is_openai_compatible())
            valid, message = validate_provider_config()
            self.assertFalse(valid)
            self.assertIn("Local models are disabled", message)

    def test_shz_cloud_requires_gateway_url_and_account_token(self):
        with patch.dict(os.environ, {"SHZ_LLM_PROVIDER": "shz-cloud"}, clear=True):
            valid, message = validate_provider_config()
            self.assertFalse(valid)
            self.assertIn("endpoint URL", message)

    def test_shz_cloud_configuration(self):
        env = {
            "SHZ_LLM_PROVIDER": "shz-cloud",
            "SHZ_CLOUD_BASE_URL": "https://cloud.example.test/v1",
            "SHZ_CLOUD_ACCESS_TOKEN": "account-token",
        }
        with patch.dict(os.environ, env, clear=True):
            self.assertTrue(is_openai_compatible())
            self.assertEqual(get_base_url(), "https://cloud.example.test/v1")
            self.assertTrue(validate_provider_config()[0])

    def test_hosted_provider_requires_own_key(self):
        with patch.dict(os.environ, {"SHZ_LLM_PROVIDER": "openrouter"}, clear=True):
            valid, message = validate_provider_config()
            self.assertFalse(valid)
            self.assertIn("access token or API key", message)

    def test_custom_cloud_compatible_endpoint(self):
        env = {
            "SHZ_LLM_PROVIDER": "openai-compatible",
            "SHZ_LLM_BASE_URL": "https://api.example.test/v1",
            "SHZ_LLM_API_KEY": "test-token",
        }
        with patch.dict(os.environ, env, clear=True):
            self.assertTrue(validate_provider_config()[0])
            self.assertEqual(get_base_url(), "https://api.example.test/v1")


if __name__ == "__main__":
    unittest.main()
