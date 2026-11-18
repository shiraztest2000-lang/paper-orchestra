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
            self.assertIn("مدل محلی غیرفعال", message)

    def test_shz_gateway_is_disabled(self):
        with patch.dict(os.environ, {"SHZ_LLM_PROVIDER": "shz-cloud"}, clear=True):
            valid, message = validate_provider_config()
            self.assertFalse(valid)
            self.assertIn("درگاه مرکزی SHZ", message)

    def test_gemini_requires_account_key_or_vertex(self):
        with patch.dict(os.environ, {"SHZ_LLM_PROVIDER": "gemini"}, clear=True):
            self.assertFalse(validate_provider_config()[0])
        with patch.dict(os.environ, {"SHZ_LLM_PROVIDER": "gemini", "GEMINI_API_KEY": "test"}, clear=True):
            self.assertTrue(validate_provider_config()[0])

    def test_gemini_model_discovery_uses_generate_content(self):
        from unittest.mock import Mock, patch
        from utils.provider_config import list_gemini_models
        response = Mock()
        response.json.return_value = {
            "models": [
                {"name": "models/gemini-2.5-flash", "supportedGenerationMethods": ["generateContent"]},
                {"name": "models/embedding-001", "supportedGenerationMethods": ["embedContent"]},
            ]
        }
        response.raise_for_status.return_value = None
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}, clear=True):
            with patch("requests.get", return_value=response) as get:
                self.assertEqual(list_gemini_models(), ["gemini-2.5-flash"])
                self.assertEqual(get.call_args.kwargs["params"]["key"], "test-key")

    def test_openrouter_free_still_requires_user_key(self):
        with patch.dict(os.environ, {"SHZ_LLM_PROVIDER": "openrouter"}, clear=True):
            valid, message = validate_provider_config()
            self.assertFalse(valid)
            self.assertIn("کلید API حساب خودتان", message)

    def test_free_mode_allows_only_openrouter_free_models(self):
        env = {
            "SHZ_FREE_MODE": "true",
            "SHZ_LLM_PROVIDER": "openrouter",
            "SHZ_LLM_MODEL": "openrouter/free",
            "OPENROUTER_API_KEY": "test-token",
        }
        with patch.dict(os.environ, env, clear=True):
            self.assertTrue(validate_provider_config()[0])
            os.environ["SHZ_LLM_MODEL"] = "openai/gpt-4o"
            valid, message = validate_provider_config()
            self.assertFalse(valid)
            self.assertIn("فقط مدل‌های رایگان", message)

    def test_free_mode_rejects_paid_providers(self):
        env = {
            "SHZ_FREE_MODE": "true",
            "SHZ_LLM_PROVIDER": "openai",
            "SHZ_LLM_MODEL": "gpt-4o",
            "OPENAI_API_KEY": "test-token",
        }
        with patch.dict(os.environ, env, clear=True):
            valid, message = validate_provider_config()
            self.assertFalse(valid)
            self.assertIn("فقط به OpenRouter Free", message)

    def test_custom_key_is_not_reused_for_another_hosted_provider(self):
        env = {"SHZ_LLM_PROVIDER": "groq", "SHZ_LLM_API_KEY": "custom-key"}
        with patch.dict(os.environ, env, clear=True):
            self.assertIsNone(__import__("utils.provider_config", fromlist=["get_api_key"]).get_api_key())

    def test_hosted_provider_defaults(self):
        env = {"SHZ_LLM_PROVIDER": "cerebras", "CEREBRAS_API_KEY": "test-token"}
        with patch.dict(os.environ, env, clear=True):
            self.assertTrue(is_openai_compatible())
            self.assertEqual(get_base_url(), "https://api.cerebras.ai/v1")
            self.assertTrue(validate_provider_config()[0])

    def test_builtin_provider_ignores_custom_endpoint_environment(self):
        env = {
            "SHZ_LLM_PROVIDER": "openrouter",
            "SHZ_LLM_BASE_URL": "https://stale-custom.example.test/v1",
            "OPENROUTER_API_KEY": "test-token",
        }
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(get_base_url(), "https://openrouter.ai/api/v1")

    def test_custom_cloud_compatible_endpoint(self):
        env = {
            "SHZ_LLM_PROVIDER": "openai-compatible",
            "SHZ_LLM_BASE_URL": "https://api.example.test/v1",
            "SHZ_LLM_API_KEY": "test-token",
        }
        with patch.dict(os.environ, env, clear=True):
            self.assertTrue(validate_provider_config()[0])
            self.assertEqual(get_base_url(), "https://api.example.test/v1")

    def test_custom_remote_http_endpoint_is_rejected(self):
        env = {
            "SHZ_LLM_PROVIDER": "openai-compatible",
            "SHZ_LLM_BASE_URL": "http://api.example.test/v1",
            "SHZ_LLM_API_KEY": "test-token",
        }
        with patch.dict(os.environ, env, clear=True):
            valid, message = validate_provider_config()
            self.assertFalse(valid)
            self.assertIn("HTTPS", message)


if __name__ == "__main__":
    unittest.main()
