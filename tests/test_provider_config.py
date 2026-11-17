import os
import unittest
from unittest.mock import patch

from utils.provider_config import (
    get_base_url,
    get_provider,
    is_local_provider,
    is_openai_compatible,
    validate_provider_config,
)


class ProviderConfigTests(unittest.TestCase):
    def test_ollama_default_endpoint_and_no_key(self):
        with patch.dict(os.environ, {"SHZ_LLM_PROVIDER": "ollama"}, clear=True):
            self.assertEqual(get_provider(), "ollama")
            self.assertEqual(get_base_url(), "http://127.0.0.1:11434/v1")
            self.assertTrue(is_local_provider())
            self.assertTrue(is_openai_compatible())
            self.assertEqual(validate_provider_config()[0], True)

    def test_lm_studio_default_endpoint(self):
        with patch.dict(os.environ, {"SHZ_LLM_PROVIDER": "lmstudio"}, clear=True):
            self.assertEqual(get_base_url(), "http://127.0.0.1:1234/v1")
            self.assertTrue(validate_provider_config()[0])

    def test_cloud_provider_requires_key(self):
        with patch.dict(os.environ, {"SHZ_LLM_PROVIDER": "openrouter"}, clear=True):
            valid, message = validate_provider_config()
            self.assertFalse(valid)
            self.assertIn("API key", message)

    def test_custom_compatible_endpoint(self):
        env = {
            "SHZ_LLM_PROVIDER": "openai-compatible",
            "SHZ_LLM_BASE_URL": "http://127.0.0.1:9000/v1",
            "SHZ_LLM_API_KEY": "test-token",
        }
        with patch.dict(os.environ, env, clear=True):
            self.assertTrue(validate_provider_config()[0])
            self.assertEqual(get_base_url(), "http://127.0.0.1:9000/v1")


if __name__ == "__main__":
    unittest.main()
