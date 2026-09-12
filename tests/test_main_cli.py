"""Tests for the azure-plan CLI command."""
from __future__ import annotations

from pathlib import Path

from src.main import main

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_azure_plan_defaults_to_shipped_examples(capsys):
    rc = main(["azure-plan"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Endpoint:" in out
    assert "ml-cloud-deploy-endpoint" in out


def test_azure_plan_reports_error_for_bad_config(tmp_path, capsys):
    bad = tmp_path / "endpoint.yaml"
    bad.write_text("name: Bad_Name!\nauth_mode: key\n", encoding="utf-8")

    rc = main(
        [
            "azure-plan",
            "--endpoint",
            str(bad),
            "--deployment",
            str(REPO_ROOT / "examples" / "azure" / "deployment.yaml"),
        ]
    )
    assert rc == 1
    assert "error" in capsys.readouterr().err
