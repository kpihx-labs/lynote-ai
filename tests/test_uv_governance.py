"""Keep bootstrap and documented operational entry points UV-only."""

import os
from pathlib import Path
import re
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "detection-model-pipeline"


@pytest.mark.parametrize("exit_code", [0, 17])
def test_bootstrap_uses_uv_project_from_another_directory(tmp_path, exit_code):
    project = tmp_path / "checkout with spaces"
    scripts = project / "scripts"
    scripts.mkdir(parents=True)
    setup = scripts / "setup.sh"
    shutil.copyfile(ROOT / "scripts" / "setup.sh", setup)
    commands = tmp_path / "bin"
    commands.mkdir()
    uv = commands / "uv"
    uv.write_text(
        '#!/bin/sh\nprintf "%s\\n" "$@"\nexit ' + str(exit_code) + "\n",
        encoding="utf-8",
    )
    uv.chmod(0o755)

    result = subprocess.run(
        ["/bin/bash", str(setup)],
        cwd=tmp_path,
        env={**os.environ, "PATH": str(commands) + os.pathsep + os.defpath},
        capture_output=True,
        text=True,
    )

    assert result.returncode == exit_code
    assert result.stdout.splitlines()[:3] == ["sync", "--project", str(project)]
    if exit_code == 0:
        assert "uv run lynote-ai" in result.stdout
    else:
        assert "Environment ready" not in result.stdout


def test_operational_scripts_have_no_legacy_environment_commands():
    paths = [ROOT / "scripts" / "setup.sh", PIPELINE / "Makefile",
             PIPELINE / ".github" / "workflows" / "ci.yml"]
    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"\b(?:pip|conda)\s+(?:install|create|run)\b", text), path
        assert not re.search(r"python\d*\s+-m\s+(?:pip|venv)\b", text), path
        assert not re.search(r"(?:^|[|;&])\s*python\d*\s", text, re.M), path


def test_model_make_commands_use_explicit_hardware_profiles():
    result = subprocess.run(
        ["make", "-n", "test-all", "train", "calibrate", "eval", "serve"],
        cwd=PIPELINE,
        capture_output=True,
        text=True,
        check=True,
    )
    for script in ("pytest tests", "j_train_hier_model.py", "k_calibrate_hier_model.py",
                   "l_eval_hier_model.py", "m_serve_hier_api.py"):
        command = next(line for line in result.stdout.splitlines() if script in line)
        assert "--extra model --extra xpu python" in command


@pytest.mark.parametrize("backends", [("cpu", "xpu"), ("cpu", "cuda"), ("xpu", "cuda")])
def test_uv_rejects_mixed_hardware_profiles(backends):
    result = subprocess.run(
        ["uv", "sync", "--project", str(PIPELINE), "--python", "3.12",
         "--locked", "--offline", "--dry-run",
         "--extra", backends[0], "--extra", backends[1]],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "incompatible" in result.stderr.lower()


def test_documented_shell_examples_use_current_cli_and_uv():
    paths = [ROOT / "CONTRIBUTING.md",
             ROOT / "README.md", ROOT / "README.zh-CN.md",
             ROOT / ".claude" / "skills" / "ai-detector" / "SKILL.md"]
    paths.extend((ROOT / "docs").glob("*.md"))
    paths.extend((ROOT / "references").glob("*.md"))
    paths.extend(PIPELINE.glob("*.md"))
    paths.extend((PIPELINE / "docs").glob("*.md"))
    paths.extend((PIPELINE / "data").glob("*.md"))
    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"\b(?:pip|conda)\s+(?:install|create|run)\b", text), path
        assert not re.search(r"^(?:python\d*|ai-detect)\s", text, re.M), path
