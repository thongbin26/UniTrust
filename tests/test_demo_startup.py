import os
import signal
import subprocess
from unittest.mock import Mock

import httpx
import pytest

from scripts import start_demo as startup


def child(pid=123, code=None):
    process = Mock(pid=pid, returncode=code)
    process.poll.return_value = code
    return process


@pytest.mark.parametrize("data", [
    {"status": "degraded", "service": "UniTrust", "database": "ok"},
    {"status": "ok", "service": "Other", "database": "ok"},
    {"status": "ok", "service": "UniTrust", "database": "unavailable"},
    [],
])
def test_backend_readiness_rejects_200_without_required_components(data):
    assert not startup.backend_ready(httpx.Response(200, json=data))


def test_readiness_accepts_real_health_contract_and_frontend_plain_ok():
    assert startup.backend_ready(httpx.Response(200, json={
        "status": "ok", "service": "UniTrust", "database": "ok", "environment": "development",
    }))
    assert startup.frontend_ready(httpx.Response(200, text="ok"))
    assert not startup.frontend_ready(httpx.Response(200, text="<html>not the health endpoint</html>"))


def test_wait_detects_early_exit_before_request():
    client = Mock()
    with pytest.raises(RuntimeError, match="PID 123 exited with code 2"):
        startup.wait_ready(child(code=2), "http://localhost", startup.backend_ready, 10,
                           client=client, label="Backend")
    client.get.assert_not_called()


def test_wait_has_deadline_and_individual_request_timeout(monkeypatch):
    clock = [0.0]
    monkeypatch.setattr(startup.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(startup.time, "sleep", lambda seconds: clock.__setitem__(0, clock[0] + seconds))
    client = Mock()
    client.get.return_value = httpx.Response(503)
    with pytest.raises(RuntimeError, match="within 1s"):
        startup.wait_ready(child(), "http://localhost", startup.backend_ready, 1,
                           client=client, label="Backend")
    assert clock[0] == 1
    assert all(0 < call.kwargs["timeout"] <= 1 for call in client.get.call_args_list)


def setup_supervisor(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(startup, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(startup.preflight_demo, "main", lambda: 0)
    for name in startup.demo_environment():
        # run_demo changes only these keys, preserving unrelated test environment.
        if name in {"PYTHONPATH", "PYTHONUNBUFFERED", "PYTHONDONTWRITEBYTECODE",
                    "DENSE_LOCAL_FILES_ONLY", "HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE"}:
            monkeypatch.setenv(name, os.environ.get(name, ""))
    stopped = []
    monkeypatch.setattr(startup, "stop_process", lambda process: stopped.append(process.pid))
    return stopped


def test_backend_failure_never_starts_frontend_and_cleans_owned_process(monkeypatch, tmp_path):
    stopped = setup_supervisor(monkeypatch, tmp_path)
    spawn = Mock(return_value=child())
    monkeypatch.setattr(startup, "spawn_service", spawn)
    monkeypatch.setattr(startup, "wait_ready", Mock(side_effect=RuntimeError("not ready")))
    assert startup.run_demo() == 1
    assert spawn.call_count == 1
    assert stopped == [123]


def test_frontend_waits_for_backend_and_ctrl_c_cleans_both(monkeypatch, tmp_path):
    stopped = setup_supervisor(monkeypatch, tmp_path)
    order = []

    def spawn(arguments, log, environment):
        order.append(arguments[0])
        assert environment["DENSE_LOCAL_FILES_ONLY"] == "1"
        return child(123 if arguments[0] == "uvicorn" else 456)

    def wait(process, url, validator, timeout, **kwargs):
        order.append(kwargs["label"] + " ready")
        return 1.0

    monkeypatch.setattr(startup, "spawn_service", spawn)
    monkeypatch.setattr(startup, "wait_ready", wait)
    monkeypatch.setattr(startup.time, "sleep", Mock(side_effect=KeyboardInterrupt))
    assert startup.run_demo() == 0
    assert order == ["uvicorn", "Backend ready", "streamlit", "Frontend ready"]
    assert stopped == [456, 123]


def test_service_exit_cleans_sibling(monkeypatch, tmp_path):
    stopped = setup_supervisor(monkeypatch, tmp_path)
    monkeypatch.setattr(startup, "spawn_service", Mock(side_effect=[child(123, 2), child(456)]))
    monkeypatch.setattr(startup, "wait_ready", lambda *args, **kwargs: 1.0)
    assert startup.run_demo() == 1
    assert stopped == [456, 123]


def test_graceful_stop_targets_only_owned_process():
    process = child(321)
    startup.stop_process(process)
    expected = signal.CTRL_BREAK_EVENT if os.name == "nt" else signal.SIGINT
    process.send_signal.assert_called_once_with(expected)
    process.wait.assert_called_once_with(timeout=8)
    process.kill.assert_not_called()


@pytest.mark.skipif(os.name != "nt", reason="Windows owned-tree fallback")
def test_stop_timeout_targets_exact_owned_pid_tree(monkeypatch):
    process = child(321)
    process.wait.side_effect = [subprocess.TimeoutExpired("owned", 8), None]
    run = Mock()
    monkeypatch.setattr(startup.subprocess, "run", run)
    startup.stop_process(process)
    assert run.call_args.args[0] == ["taskkill", "/PID", "321", "/T", "/F"]


def test_environment_preserves_isolated_artifact_overrides(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///isolated.db")
    monkeypatch.setenv("RETRIEVAL_CACHE_DIR", "isolated-cache")
    environment = startup.demo_environment()
    assert environment["DATABASE_URL"] == "sqlite:///isolated.db"
    assert environment["RETRIEVAL_CACHE_DIR"] == "isolated-cache"
    assert environment["HF_HUB_OFFLINE"] == "1"
