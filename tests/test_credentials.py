from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from faceless_creator.config import Settings
from faceless_creator.credentials import CredentialStore
from faceless_creator.service import FacelessCreatorService


class CredentialsTests(unittest.TestCase):
    def test_save_and_status(self) -> None:
        env_keys = (
            "ELEVENLABS_API_KEY",
            "YOUTOMAGIC_ELEVENLABS_API_KEY",
            "OMNIROUTE_API_KEY",
            "OPENAI_API_KEY",
            "ELEVENLABS_VOICE_ID",
        )
        saved = {k: os.environ.get(k) for k in env_keys}
        try:
            for key in env_keys:
                os.environ.pop(key, None)
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                store = CredentialStore(root)
                bundle = store.save(
                    {
                        "elevenlabs_api_key": "sk_test",
                        "elevenlabs_voice_id": "voice123",
                        "omniroute_api_key": "omni_test",
                    }
                )
                self.assertTrue(bundle.elevenlabs_api_key)
                status = bundle.status()
                self.assertTrue(status["elevenlabs"])
                self.assertTrue(status["omniroute"])
                self.assertEqual(os.environ.get("ELEVENLABS_API_KEY"), "sk_test")

                service = FacelessCreatorService(Settings.for_root(root / "fc"))
                result = service.save_credentials(
                    {"elevenlabs_api_key": "sk_svc", "elevenlabs_voice_id": "v1"}
                )
                self.assertTrue(result["ok"])
                self.assertTrue(result["status"]["elevenlabs"])
        finally:
            for key, value in saved.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


if __name__ == "__main__":
    unittest.main()
