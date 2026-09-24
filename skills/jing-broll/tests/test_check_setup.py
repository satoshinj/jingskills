"""Offline checks for backend-scoped preflight; no real credentials or API calls."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_setup.sh"


class CheckSetupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = {
            "PATH": str(self.root),
            "HOME": os.environ["HOME"],
            "JING_BROLL_VENV": str(self.root / "missing-venv"),
            "TEST_GENAI_STATUS": "1",
        }
        for name in ("ffmpeg", "ffprobe"):
            self.command(name, "exit 0\n")
        self.command(
            "python3",
            'if [ "$1" = "-" ]; then\n'
            '  /bin/cat >/dev/null\n'
            '  exit "${TEST_GENAI_STATUS:-0}"\n'
            'fi\n'
            'case "$*" in\n'
            '  *httpx*) exit "${TEST_HTTPX_STATUS:-0}" ;;\n'
            '  *) exit 0 ;;\n'
            'esac\n',
        )

    def command(self, name, body):
        path = self.root / name
        path.write_text("#!/bin/sh\n" + body)
        path.chmod(0o700)

    def run_check(self, *args):
        return subprocess.run(
            ["/bin/bash", str(SCRIPT), *args],
            env=self.env,
            text=True,
            capture_output=True,
            timeout=5,
        )

    def test_core_route_does_not_require_gemini(self):
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("SKIP", result.stdout)

    def test_selected_gemini_requires_key(self):
        result = self.run_check("--require-gemini")
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL  GEMINI_API_KEY", result.stdout)

    def test_selected_gemini_requires_sdk(self):
        self.env["GEMINI_API_KEY"] = "offline-test-placeholder"
        result = self.run_check("--require-gemini")
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL  google-genai", result.stdout)
        self.assertNotIn(self.env["GEMINI_API_KEY"], result.stdout + result.stderr)

    def test_gemini_ready_does_not_require_fal_or_say(self):
        self.env.update(GEMINI_API_KEY="offline-test-placeholder", TEST_GENAI_STATUS="0")
        result = self.run_check("--require-gemini")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn(self.env["GEMINI_API_KEY"], result.stdout + result.stderr)

    def test_fal_route_does_not_require_gemini(self):
        self.env["FAL_KEY"] = "offline-fal-placeholder"
        result = self.run_check("--require-fal")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn(self.env["FAL_KEY"], result.stdout + result.stderr)

    def test_selected_fal_requires_key_and_httpx(self):
        result = self.run_check("--require-fal")
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL  FAL_KEY", result.stdout)
        self.env.update(FAL_KEY="offline-fal-placeholder", TEST_HTTPX_STATUS="1")
        result = self.run_check("--require-fal")
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL  httpx", result.stdout)

    def test_say_is_required_only_when_selected(self):
        result = self.run_check("--require-say")
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL  say", result.stdout)
        self.command("say", "exit 0\n")
        result = self.run_check("--require-say")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_core_tool_still_fails(self):
        (self.root / "ffmpeg").unlink()
        result = self.run_check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAIL  ffmpeg", result.stdout)

    def test_unknown_option_is_not_silently_ignored(self):
        result = self.run_check("--require-unknown")
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
