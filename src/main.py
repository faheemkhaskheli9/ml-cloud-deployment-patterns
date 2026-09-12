"""CLI entrypoint for the cloud deployment examples.

Phase 2 adds offline validation for the Azure ML deployment configs (no
Azure credentials required -- it never calls the Azure ML SDK/API):

    python -m src.main azure-plan --endpoint examples/azure/endpoint.yaml \\
        --deployment examples/azure/deployment.yaml
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.azure_deploy import AzureDeployConfigError, plan_deployment

DEFAULT_AZURE_ENDPOINT = Path("examples/azure/endpoint.yaml")
DEFAULT_AZURE_DEPLOYMENT = Path("examples/azure/deployment.yaml")


def _cmd_azure_plan(args: argparse.Namespace) -> int:
    try:
        plan = plan_deployment(args.endpoint, args.deployment)
    except AzureDeployConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(plan.summary())
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ml-cloud-deploy", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_azure = sub.add_parser(
        "azure-plan",
        help="Validate Azure ML endpoint/deployment YAML and print a dry-run plan.",
    )
    p_azure.add_argument("--endpoint", type=Path, default=DEFAULT_AZURE_ENDPOINT)
    p_azure.add_argument("--deployment", type=Path, default=DEFAULT_AZURE_DEPLOYMENT)
    p_azure.set_defaults(func=_cmd_azure_plan)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
