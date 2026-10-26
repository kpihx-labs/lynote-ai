"""Typer help tree, errors, JSON purity and backward-compatible invocations."""

import json

import pytest
from typer.testing import CliRunner

from aidetect.cli import app, main
from aidetect.core import analyze_text

runner = CliRunner()


@pytest.mark.parametrize("args,expected", [
    (["--help"], "Reference"),
    (["scan", "--help"], "Examples"),
    (["compare", "--help"], "first"),
    (["info", "--help"], "multilingual"),
    (["--help-all"], "lynote-ai compare"),
])
def test_help(args, expected):
    result = runner.invoke(app, args)
    assert result.exit_code == 0, result.output
    assert expected in result.output


def test_json_keeps_original_core_scores():
    text = "This sample contains several ordinary words for testing the analyzer. " * 30
    result = runner.invoke(app, ["scan", "--text", text, "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["score"] == analyze_text(text).score
    assert data["signals"] == analyze_text(text).to_dict()["signals"]
    assert data["timings"]["analysis_seconds"] >= 0


def test_info_is_honest_about_languages():
    result = runner.invoke(app, ["info", "--json"])
    data = json.loads(result.stdout)
    assert data["neural_model"] is None
    assert data["lexical_language"] == "en"
    assert data["calibrated_languages"] == []


@pytest.mark.parametrize("args", [
    ["scan", "missing-file.txt"],
    ["scan", "--text", " ", "--json"],
    ["scan", "--text", "hello", "--file", "other.txt"],
])
def test_clean_errors(args):
    result = runner.invoke(app, args)
    assert result.exit_code != 0
    assert "Traceback" not in result.output


def test_legacy_file_invocation(tmp_path, capsys):
    path = tmp_path / "sample.txt"
    path.write_text("Ordinary words in a short test.", encoding="utf-8")
    assert main([str(path), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["verdict"] == "insufficient_text"


def test_compare(tmp_path):
    one, two = tmp_path / "one.txt", tmp_path / "two.txt"
    one.write_text("One short document.", encoding="utf-8")
    two.write_text("Another short document.", encoding="utf-8")
    result = runner.invoke(app, ["compare", str(one), str(two), "--json"])
    assert result.exit_code == 0
    assert len(json.loads(result.stdout)) == 2
