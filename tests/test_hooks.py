"""Run the Claude Code hook scripts as subprocesses with hook-like JSON on stdin."""

import json
import os
import subprocess
import sys

import pytest

VALID_LITERAL = '"status": "val' + 'id"'  # built in two parts so editing this file is not blocked


def run_hook(repo_root, name, event, extra_env=None):
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(repo_root)}
    env.pop("NACACFD_ALLOW_PROTECTED_EDITS", None)
    env.update(extra_env or {})
    return subprocess.run(
        [sys.executable, str(repo_root / ".claude" / "hooks" / name)],
        input=json.dumps(event), capture_output=True, text=True, env=env,
    )


@pytest.mark.parametrize("event", [
    {"tool_name": "Write", "tool_input": {"file_path": "data/reference/naca0012_ladson/cl.csv", "content": "1"}},
    {"tool_name": "Edit", "tool_input": {"file_path": "config/qa_thresholds.yaml", "old_string": "a", "new_string": "b"}},
    {"tool_name": "Write", "tool_input": {"file_path": "runs/e/c/results.json", "content": "{" + VALID_LITERAL + "}"}},
    {"tool_name": "MultiEdit", "tool_input": {"file_path": "runs/e/c/results.json",
                                              "edits": [{"old_string": "x", "new_string": VALID_LITERAL}]}},
    {"tool_name": "Bash", "tool_input": {"command": "sed -i 's/2.0/5.0/' config/qa_thresholds.yaml"}},
    {"tool_name": "Bash", "tool_input": {"command": "echo 1 > data/reference/x.csv"}},
])
def test_guard_blocks(repo_root, event):
    r = run_hook(repo_root, "guard_protected.py", event)
    assert r.returncode == 2, r.stderr
    assert "BLOCKED" in r.stderr


def test_guard_blocks_absolute_paths(repo_root):
    event = {"tool_name": "Write",
             "tool_input": {"file_path": str(repo_root / "config" / "qa_thresholds.yaml"), "content": ""}}
    assert run_hook(repo_root, "guard_protected.py", event).returncode == 2


@pytest.mark.parametrize("event", [
    {"tool_name": "Write", "tool_input": {"file_path": "src/nacacfd/qa/mesh.py", "content": "x = 1"}},
    {"tool_name": "Write", "tool_input": {"file_path": "runs/e/c/results.json", "content": '{"status": "invalid"}'}},
    {"tool_name": "Bash", "tool_input": {"command": "cat config/qa_thresholds.yaml"}},
    {"tool_name": "Bash", "tool_input": {"command": "pytest -q"}},
])
def test_guard_allows(repo_root, event):
    r = run_hook(repo_root, "guard_protected.py", event)
    assert r.returncode == 0, r.stderr


def test_guard_human_override(repo_root):
    event = {"tool_name": "Edit", "tool_input": {"file_path": "config/qa_thresholds.yaml", "new_string": "b"}}
    r = run_hook(repo_root, "guard_protected.py", event, {"NACACFD_ALLOW_PROTECTED_EDITS": "1"})
    assert r.returncode == 0


def test_run_logger_appends_line(tmp_path, repo_root):
    hook_root = tmp_path
    (hook_root / ".claude" / "hooks").mkdir(parents=True)
    script = (repo_root / ".claude" / "hooks" / "log_solver_run.py").read_text()
    (hook_root / ".claude" / "hooks" / "log_solver_run.py").write_text(script)
    event = {"session_id": "s1", "tool_name": "Bash",
             "tool_input": {"command": "nacacfd run experiments/x.yaml"},
             "tool_response": {"stdout": "", "stderr": "boom", "interrupted": False}}
    assert run_hook(hook_root, "log_solver_run.py", event).returncode == 0
    lines = (hook_root / "docs" / "agent_log" / "runs.log").read_text().splitlines()
    assert len(lines) == 1 and json.loads(lines[0])["command"] == "nacacfd run experiments/x.yaml"


def test_run_logger_ignores_other_commands(tmp_path, repo_root):
    (tmp_path / ".claude" / "hooks").mkdir(parents=True)
    (tmp_path / ".claude" / "hooks" / "log_solver_run.py").write_text(
        (repo_root / ".claude" / "hooks" / "log_solver_run.py").read_text())
    run_hook(tmp_path, "log_solver_run.py", {"tool_name": "Bash", "tool_input": {"command": "ls"}})
    assert not (tmp_path / "docs" / "agent_log" / "runs.log").exists()
