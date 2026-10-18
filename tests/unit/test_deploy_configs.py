"""Deploy/CD contract tests — the config files must keep their safety- and deploy-critical shape."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]


def _json(name: str) -> dict:
    return json.loads((REPO_ROOT / name).read_text(encoding="utf-8"))


def _yaml(name: str) -> dict:
    return yaml.safe_load((REPO_ROOT / name).read_text(encoding="utf-8"))


def test_vercel_rewrites_deep_links_to_index() -> None:
    config = _json("vercel.json")
    destinations = {rewrite["destination"] for rewrite in config["rewrites"]}
    assert "/index.html" in destinations


def test_web_vercel_config_is_a_self_contained_fallback() -> None:
    # Safety net: if the Vercel project's Root Directory is set to `web`, the repo-root
    # vercel.json is ignored. web/vercel.json must still provide SPA routing + build.
    config = _json("web/vercel.json")
    destinations = {rewrite["destination"] for rewrite in config["rewrites"]}
    assert "/index.html" in destinations
    assert config["outputDirectory"] == "dist"
    assert config["buildCommand"] == "npm run build"


def test_vercel_caches_immutable_assets() -> None:
    config = _json("vercel.json")
    asset_rule = next(
        (rule for rule in config.get("headers", []) if rule["source"] == "/assets/(.*)"),
        None,
    )
    assert asset_rule is not None, "missing immutable cache rule for /assets"
    cache = " ".join(
        header["value"].lower()
        for header in asset_rule["headers"]
        if header["key"].lower() == "cache-control"
    )
    assert "immutable" in cache
    assert "max-age" in cache


def test_vercel_sets_spa_security_headers() -> None:
    config = _json("vercel.json")
    keys = {
        header["key"].lower()
        for rule in config.get("headers", [])
        for header in rule["headers"]
    }
    assert "x-content-type-options" in keys
    assert "x-frame-options" in keys
    assert "referrer-policy" in keys


def test_railway_healthcheck_points_at_liveness() -> None:
    config = _json("railway.json")
    assert config["deploy"]["healthcheckPath"] == "/health"
    assert config["build"]["builder"] == "DOCKERFILE"


def test_render_blueprint_uses_health_check_and_keeps_secrets_out_of_repo() -> None:
    config = _yaml("render.yaml")
    service = config["services"][0]
    assert service["runtime"] == "docker"
    assert service["healthCheckPath"] == "/health"
    secret = next(env for env in service["envVars"] if env["key"] == "SUPABASE_SECRET_KEY")
    assert secret.get("sync") is False
    assert "value" not in secret


def _workflow(name: str) -> dict:
    data = _yaml(f".github/workflows/{name}")
    # PyYAML parses the bare `on:` key as boolean True.
    return data


def test_ci_workflow_runs_required_stages() -> None:
    workflow = _workflow("ci.yml")
    jobs = set(workflow["jobs"])
    assert {"lint", "backend-tests", "frontend-tests", "security", "e2e", "docker"} <= jobs


def test_deploy_workflow_triggers_after_ci_on_main_only() -> None:
    workflow = _workflow("deploy.yml")
    triggers = workflow.get(True) or workflow.get("on")
    assert "workflow_run" in triggers
    deploy_jobs = {name: job for name, job in workflow["jobs"].items() if name.startswith("deploy-")}
    assert deploy_jobs, "expected deploy-* jobs"
    for job_name, job in deploy_jobs.items():
        condition = " ".join(job["if"].split())
        assert "head_branch == 'main'" in condition, job_name
        assert "head_repository.full_name == github.repository" in condition, job_name


def test_deploy_workflow_smoke_checks_live_endpoints() -> None:
    workflow = _workflow("deploy.yml")
    smoke = workflow["jobs"].get("smoke")
    assert smoke is not None, "missing post-deploy smoke job"
    needs = smoke.get("needs")
    needs = needs if isinstance(needs, list) else [needs]
    assert {"deploy-frontend", "deploy-backend"} <= set(needs)
    haystack = "\n".join(step.get("run", "") for step in smoke["steps"]) + "\n" + str(smoke.get("env"))
    assert "/health/ready" in haystack
    assert '"status":"ready"' in haystack


def test_dockerfile_installs_workspace_members() -> None:
    text = (REPO_ROOT / "Dockerfile").read_text(encoding="utf-8")
    # Regression guard: --no-install-project does not skip workspace members and breaks the build.
    assert "--no-install-workspace" in text
    assert "--no-install-project" not in text
