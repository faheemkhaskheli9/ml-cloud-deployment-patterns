"""Tests for the Phase 2 Azure ML deployment config validator (offline, no
Azure credentials or network calls -- see src/azure_deploy.py)."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from src.azure_deploy import (
    AzureDeployConfigError,
    load_deployment_config,
    load_endpoint_config,
    plan_deployment,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SHIPPED_ENDPOINT = REPO_ROOT / "examples" / "azure" / "endpoint.yaml"
SHIPPED_DEPLOYMENT = REPO_ROOT / "examples" / "azure" / "deployment.yaml"


def _write(tmp_path: Path, name: str, text: str) -> Path:
    p = tmp_path / name
    p.write_text(textwrap.dedent(text), encoding="utf-8")
    return p


def test_shipped_endpoint_and_deployment_configs_are_valid():
    plan = plan_deployment(SHIPPED_ENDPOINT, SHIPPED_DEPLOYMENT)
    assert plan.endpoint.name == "ml-cloud-deploy-endpoint"
    assert plan.deployment.endpoint_name == plan.endpoint.name
    assert "Endpoint:" in plan.summary()


def test_missing_endpoint_config_is_a_hard_error(tmp_path):
    with pytest.raises(AzureDeployConfigError, match="not found"):
        load_endpoint_config(tmp_path / "nope.yaml")


def test_bad_endpoint_name_is_rejected(tmp_path):
    p = _write(tmp_path, "endpoint.yaml", "name: Bad_Name!\nauth_mode: key\n")
    with pytest.raises(AzureDeployConfigError, match="naming rule"):
        load_endpoint_config(p)


def test_unknown_auth_mode_is_rejected(tmp_path):
    p = _write(tmp_path, "endpoint.yaml", "name: my-endpoint\nauth_mode: password\n")
    with pytest.raises(AzureDeployConfigError, match="auth_mode"):
        load_endpoint_config(p)


def test_deployment_missing_instance_type_is_rejected(tmp_path):
    p = _write(
        tmp_path,
        "deployment.yaml",
        """
        name: blue
        endpoint_name: my-endpoint
        environment:
          image: myacr.azurecr.io/img:latest
        code_configuration:
          scoring_script: score.py
        """,
    )
    with pytest.raises(AzureDeployConfigError, match="instance_type"):
        load_deployment_config(p)


def test_deployment_missing_environment_image_is_rejected(tmp_path):
    p = _write(
        tmp_path,
        "deployment.yaml",
        """
        name: blue
        endpoint_name: my-endpoint
        instance_type: Standard_DS2_v2
        code_configuration:
          scoring_script: score.py
        """,
    )
    with pytest.raises(AzureDeployConfigError, match="environment.image"):
        load_deployment_config(p)


def test_deployment_missing_scoring_script_is_rejected(tmp_path):
    p = _write(
        tmp_path,
        "deployment.yaml",
        """
        name: blue
        endpoint_name: my-endpoint
        instance_type: Standard_DS2_v2
        environment:
          image: myacr.azurecr.io/img:latest
        """,
    )
    with pytest.raises(AzureDeployConfigError, match="scoring_script"):
        load_deployment_config(p)


def test_invalid_traffic_percentage_is_rejected(tmp_path):
    p = _write(
        tmp_path,
        "deployment.yaml",
        """
        name: blue
        endpoint_name: my-endpoint
        instance_type: Standard_DS2_v2
        environment:
          image: myacr.azurecr.io/img:latest
        code_configuration:
          scoring_script: score.py
        traffic_percentage: 150
        """,
    )
    with pytest.raises(AzureDeployConfigError, match="traffic_percentage"):
        load_deployment_config(p)


def test_mismatched_endpoint_names_are_rejected(tmp_path):
    endpoint = _write(tmp_path, "endpoint.yaml", "name: endpoint-a\nauth_mode: key\n")
    deployment = _write(
        tmp_path,
        "deployment.yaml",
        """
        name: blue
        endpoint_name: endpoint-b
        instance_type: Standard_DS2_v2
        environment:
          image: myacr.azurecr.io/img:latest
        code_configuration:
          scoring_script: score.py
        """,
    )
    with pytest.raises(AzureDeployConfigError, match="does not match"):
        plan_deployment(endpoint, deployment)


def test_high_instance_count_triggers_a_quota_warning(tmp_path):
    endpoint = _write(tmp_path, "endpoint.yaml", "name: my-endpoint\nauth_mode: key\n")
    deployment = _write(
        tmp_path,
        "deployment.yaml",
        """
        name: blue
        endpoint_name: my-endpoint
        instance_type: Standard_DS3_v2
        instance_count: 4
        environment:
          image: myacr.azurecr.io/img:latest
        code_configuration:
          scoring_script: score.py
        traffic_percentage: 0
        """,
    )
    plan = plan_deployment(endpoint, deployment)
    assert any("quota" in w for w in plan.warnings)


def test_full_traffic_on_first_rollout_triggers_a_warning(tmp_path):
    endpoint = _write(tmp_path, "endpoint.yaml", "name: my-endpoint\nauth_mode: key\n")
    deployment = _write(
        tmp_path,
        "deployment.yaml",
        """
        name: blue
        endpoint_name: my-endpoint
        instance_type: Standard_DS2_v2
        environment:
          image: myacr.azurecr.io/img:latest
        code_configuration:
          scoring_script: score.py
        traffic_percentage: 100
        """,
    )
    plan = plan_deployment(endpoint, deployment)
    assert any("traffic_percentage=100" in w for w in plan.warnings)


def test_unrecognized_instance_type_triggers_a_warning_not_an_error(tmp_path):
    endpoint = _write(tmp_path, "endpoint.yaml", "name: my-endpoint\nauth_mode: key\n")
    deployment = _write(
        tmp_path,
        "deployment.yaml",
        """
        name: blue
        endpoint_name: my-endpoint
        instance_type: Standard_NC6s_v3
        environment:
          image: myacr.azurecr.io/img:latest
        code_configuration:
          scoring_script: score.py
        traffic_percentage: 0
        """,
    )
    plan = plan_deployment(endpoint, deployment)
    assert any("not in the recorded quota reference table" in w for w in plan.warnings)
