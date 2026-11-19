"""Guard against accidentally weakening the hardened pilot Compose overlay.

This test validates effective Compose configuration without starting containers.
"""
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]


def test_pilot_compose_isolation(tmp_path):
    if shutil.which("docker") is None:
        pytest.skip("Docker CLI not available on this test machine")
    env_file = tmp_path / "suparagent.env"
    env_file.write_text("", encoding="utf-8")
    env = dict(os.environ)
    env["SUPARAGENT_ENV_FILE"] = str(env_file)
    # Host overrides are not allowed in this reproducible CI security check.
    env["SUPARAGENT_BIND"] = "0.0.0.0"  # deliberate hostile override: overlay must win.
    for key in ("SUPARAGENT_PORT", "SUPARAGENT_IMAGE",
                "SUPARAGENT_SUBNET", "SUPARAGENT_GATEWAY",
                "SUPARAGENT_DYNAMIC_RANGE"):
        env.pop(key, None)
    result = subprocess.run(
        ["docker", "compose", "-f", str(ROOT / "compose.yaml"),
         "-f", str(ROOT / "deploy/compose.hardened.yaml"),
         "config", "--format", "json"],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    service = json.loads(result.stdout)["services"]["suparagent"]
    assert service.get("read_only") is True
    assert "ALL" in service.get("cap_drop", [])
    assert any(flag.replace("=", ":") == "no-new-privileges:true"
               for flag in service.get("security_opt", []))
    assert service["pids_limit"] == 256
    assert service["ports"][0]["host_ip"] == "127.0.0.1"
    assert all(volume["type"] == "volume" for volume in service["volumes"])
    assert service.get("privileged", False) is False
