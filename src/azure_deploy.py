"""Azure ML managed online endpoint deployment plan (Phase 2).

This module does **not** call the Azure ML SDK or any network endpoint --
that would require real Azure credentials and quota this CPU-only sandbox
doesn't have. Instead it parses and validates the same declarative YAML the
real `az ml online-endpoint create` / `az ml online-deployment create` CLI
v2 commands consume (see ``examples/azure/*.yaml``), and produces a
human-readable deployment plan. This is the boundary a real Azure deployment
would fill in behind the same validated config -- see
``scripts/deploy_azure.sh`` for the actual `az` commands an operator with
real credentials would run against this same YAML.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

# Azure ML endpoint/deployment names: lowercase alphanumeric + hyphens,
# must start with a letter, 3-32 chars (Azure ML's actual naming rule).
_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9-]{2,31}$")

# Azure ML online-deployment quota is charged per (instance_type, region) pair
# and defaults to a handful of cores per subscription -- a deployment sized
# above the default quota fails at `az ml online-deployment create`, not at
# validation time, unless a quota increase was requested in advance.
KNOWN_INSTANCE_TYPES = {
    "Standard_DS2_v2": 2,
    "Standard_DS3_v2": 4,
    "Standard_F4s_v2": 4,
}


class AzureDeployConfigError(ValueError):
    """Raised when an endpoint/deployment YAML fails to parse or validate."""


@dataclass(frozen=True)
class EndpointConfig:
    name: str
    auth_mode: str
    description: str = ""


@dataclass(frozen=True)
class DeploymentConfig:
    name: str
    endpoint_name: str
    instance_type: str
    instance_count: int
    environment_image: str
    scoring_script: str
    traffic_percentage: int = 100


@dataclass(frozen=True)
class DeploymentPlan:
    endpoint: EndpointConfig
    deployment: DeploymentConfig
    warnings: list[str]

    def summary(self) -> str:
        lines = [
            f"Endpoint:    {self.endpoint.name} (auth_mode={self.endpoint.auth_mode})",
            f"Deployment:  {self.deployment.name} -> {self.deployment.endpoint_name}",
            f"Instance:    {self.deployment.instance_type} x{self.deployment.instance_count}",
            f"Image:       {self.deployment.environment_image}",
            f"Scoring:     {self.deployment.scoring_script}",
            f"Traffic:     {self.deployment.traffic_percentage}%",
        ]
        if self.warnings:
            lines.append("Warnings:")
            lines.extend(f"  - {w}" for w in self.warnings)
        return "\n".join(lines)


def _load_yaml(path: str | Path) -> dict:
    p = Path(path)
    if not p.is_file():
        raise AzureDeployConfigError(f"config file not found: {p}")
    raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise AzureDeployConfigError(f"expected a mapping at the top level of {p}")
    return raw


def _require_name(name: object, *, field: str) -> str:
    if not isinstance(name, str) or not _NAME_PATTERN.match(name):
        raise AzureDeployConfigError(
            f"{field} must be lowercase alphanumeric/hyphens, start with a letter, "
            f"3-32 chars (Azure ML naming rule); got {name!r}"
        )
    return name


def load_endpoint_config(path: str | Path) -> EndpointConfig:
    raw = _load_yaml(path)
    name = _require_name(raw.get("name"), field="endpoint name")
    auth_mode = raw.get("auth_mode", "key")
    if auth_mode not in ("key", "aml_token"):
        raise AzureDeployConfigError(f"unknown auth_mode: {auth_mode!r} (expected 'key' or 'aml_token')")
    return EndpointConfig(name=name, auth_mode=auth_mode, description=raw.get("description", ""))


def load_deployment_config(path: str | Path) -> DeploymentConfig:
    raw = _load_yaml(path)
    name = _require_name(raw.get("name"), field="deployment name")
    endpoint_name = _require_name(raw.get("endpoint_name"), field="endpoint_name")

    instance_type = raw.get("instance_type")
    if not instance_type:
        raise AzureDeployConfigError("instance_type is required")

    instance_count = raw.get("instance_count", 1)
    if not isinstance(instance_count, int) or instance_count < 1:
        raise AzureDeployConfigError(f"instance_count must be a positive int, got {instance_count!r}")

    environment_image = raw.get("environment", {}).get("image") if isinstance(raw.get("environment"), dict) else None
    if not environment_image:
        raise AzureDeployConfigError("environment.image is required (the Docker image to deploy)")

    scoring_script = raw.get("code_configuration", {}).get("scoring_script")
    if not scoring_script:
        raise AzureDeployConfigError("code_configuration.scoring_script is required")

    traffic_percentage = raw.get("traffic_percentage", 100)
    if not isinstance(traffic_percentage, int) or not 0 <= traffic_percentage <= 100:
        raise AzureDeployConfigError(f"traffic_percentage must be 0-100, got {traffic_percentage!r}")

    return DeploymentConfig(
        name=name,
        endpoint_name=endpoint_name,
        instance_type=instance_type,
        instance_count=instance_count,
        environment_image=environment_image,
        scoring_script=scoring_script,
        traffic_percentage=traffic_percentage,
    )


def plan_deployment(endpoint_path: str | Path, deployment_path: str | Path) -> DeploymentPlan:
    """Validate an endpoint + deployment config pair and return a dry-run plan.

    Never calls Azure -- this is offline validation only, so it runs (and is
    tested) without any cloud credentials.
    """
    endpoint = load_endpoint_config(endpoint_path)
    deployment = load_deployment_config(deployment_path)

    if deployment.endpoint_name != endpoint.name:
        raise AzureDeployConfigError(
            f"deployment.endpoint_name ({deployment.endpoint_name!r}) does not match "
            f"endpoint.name ({endpoint.name!r})"
        )

    warnings: list[str] = []
    if deployment.instance_type not in KNOWN_INSTANCE_TYPES:
        warnings.append(
            f"instance_type {deployment.instance_type!r} is not in the recorded quota "
            f"reference table -- verify it against your subscription's available SKUs "
            f"before deploying (`az vm list-skus --location <region>`)."
        )
    else:
        cores = KNOWN_INSTANCE_TYPES[deployment.instance_type]
        total_cores = cores * deployment.instance_count
        if total_cores > 4:
            warnings.append(
                f"{deployment.instance_count}x {deployment.instance_type} requests "
                f"{total_cores} vCPUs -- default Azure ML online-endpoint quota per "
                f"subscription/region is small; request a quota increase in advance "
                f"or the deployment will fail at `az ml online-deployment create`, "
                f"not at validation time."
            )
    if deployment.traffic_percentage == 100:
        warnings.append(
            "traffic_percentage=100 sends all live traffic to this deployment "
            "immediately -- for a first rollout, deploy at 0% and shift traffic "
            "with `az ml online-endpoint update` after a smoke test."
        )

    return DeploymentPlan(endpoint=endpoint, deployment=deployment, warnings=warnings)
