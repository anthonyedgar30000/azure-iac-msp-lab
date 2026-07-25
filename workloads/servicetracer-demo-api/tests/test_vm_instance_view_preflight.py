from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "workloads/servicetracer-demo-api/scripts/assert_vm_instance_view.py"
FIXTURE = ROOT / "workloads/servicetracer-demo-api/tests/fixtures/vm-instance-view-nested-statuses.json"
WORKFLOW = ROOT / ".github/workflows/servicetracer-demo-api-timeout-fix-deploy-retry.yml"

spec = importlib.util.spec_from_file_location("assert_vm_instance_view", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_nested_instance_view_statuses_report_running() -> None:
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    statuses = module.extract_statuses(document)
    assert [item["code"] for item in statuses][-1] == "PowerState/running"


def test_top_level_statuses_remain_supported() -> None:
    document = {"statuses": [{"code": "PowerState/running"}]}
    assert module.extract_statuses(document) == document["statuses"]


def test_missing_statuses_fail_closed() -> None:
    assert module.extract_statuses({"instanceView": {"statuses": None}}) == []


def test_retry_workflow_is_null_safe_for_both_cli_shapes() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert '.statuses // .instanceView.statuses // []' in workflow
    assert ".statuses | any(.code" not in workflow
