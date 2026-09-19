"""Own the two demo services, readiness checks, and bounded cleanup."""

import argparse
from contextlib import ExitStack
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import httpx

from scripts import preflight_demo


def demo_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment.update({
        "PYTHONPATH": str(PROJECT_ROOT),
        "PYTHONUNBUFFERED": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "DENSE_LOCAL_FILES_ONLY": "1",
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
    })
    return environment


def backend_ready(response: httpx.Response) -> bool:
    try:
        data = response.json()
        return response.status_code == 200 and all(
            data.get(key) == value
            for key, value in (("status", "ok"), ("service", "UniTrust"), ("database", "ok"))
        )
    except (ValueError, AttributeError):
        return False


def frontend_ready(response: httpx.Response) -> bool:
    return response.status_code == 200 and response.text.strip() == "ok"


def wait_ready(process, url, validator, timeout, *, client, label, dependencies=()) -> float:
    started = time.monotonic()
    deadline = started + timeout
    last_problem = "no response yet"
    while time.monotonic() < deadline:
        for child in (process, *dependencies):
            if child.poll() is not None:
                raise RuntimeError(f"{label}: process PID {child.pid} exited with code {child.returncode}.")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        try:
            response = client.get(url, timeout=min(2.0, remaining))
            if validator(response):
                return time.monotonic() - started
            last_problem = f"HTTP {response.status_code}, readiness condition not met"
        except httpx.HTTPError as exc:
            last_problem = type(exc).__name__
        time.sleep(min(0.25, max(0, deadline - time.monotonic())))
    raise RuntimeError(f"{label} was not ready within {timeout:g}s ({last_problem}).")


def stop_process(process, grace: float = 8) -> None:
    """Signal only this owned process group; force it only after a grace period."""
    if process.poll() is not None:
        return
    print(f"Stopping owned process PID {process.pid}...", flush=True)
    try:
        if os.name == "nt":
            process.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            process.send_signal(signal.SIGINT)
        process.wait(timeout=grace)
        return
    except (OSError, subprocess.TimeoutExpired):
        pass
    if process.poll() is not None:
        return
    print(f"Graceful shutdown timed out; stopping owned PID {process.pid} and its children.", flush=True)
    if os.name == "nt":
        # A Windows venv launcher can own a child Python process. /T follows
        # only this known, still-running parent's process tree.
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            capture_output=True, timeout=10, check=False,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    else:
        process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def spawn_service(arguments, log, environment):
    options = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {}
    return subprocess.Popen(
        [sys.executable, "-B", "-u", "-m", *arguments],
        cwd=PROJECT_ROOT, env=environment, stdout=log, stderr=subprocess.STDOUT,
        **options,
    )


def log_tail(path: Path, limit: int = 18) -> None:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        if lines:
            print(f"--- {path.name}: last {limit} lines ---")
            print("\n".join(lines[-limit:]))
    except OSError:
        pass


def run_demo(backend_timeout: float = 180, frontend_timeout: float = 60) -> int:
    os.chdir(PROJECT_ROOT)
    environment = demo_environment()
    os.environ.update({key: environment[key] for key in (
        "PYTHONPATH", "PYTHONUNBUFFERED", "PYTHONDONTWRITEBYTECODE",
        "DENSE_LOCAL_FILES_ONLY", "HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE",
    )})
    started = time.monotonic()
    if preflight_demo.main() != 0:
        return 1
    log_directory = PROJECT_ROOT / "tmp/demo"
    log_directory.mkdir(parents=True, exist_ok=True)
    backend_log = log_directory / "backend.log"
    frontend_log = log_directory / "frontend.log"
    processes = []
    try:
        with ExitStack() as stack:
            backend_output = stack.enter_context(backend_log.open("w", encoding="utf-8"))
            frontend_output = stack.enter_context(frontend_log.open("w", encoding="utf-8"))
            client = stack.enter_context(httpx.Client(trust_env=False))
            backend = spawn_service(["uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"], backend_output, environment)
            processes.append(backend)
            print(f"Starting backend PID {backend.pid}; log: {backend_log}", flush=True)
            backend_seconds = wait_ready(backend, "http://127.0.0.1:8000/health", backend_ready,
                                         backend_timeout, client=client, label="Backend")
            print(f"Backend ready in {backend_seconds:.2f}s ({time.monotonic() - started:.2f}s since launcher).", flush=True)
            frontend = spawn_service([
                "streamlit", "run", str(PROJECT_ROOT / "frontend/Home.py"),
                "--server.port", "8501", "--server.address", "127.0.0.1", "--server.headless", "true",
            ], frontend_output, environment)
            processes.append(frontend)
            frontend_seconds = wait_ready(frontend, "http://127.0.0.1:8501/_stcore/health", frontend_ready,
                                          frontend_timeout, client=client, label="Frontend", dependencies=(backend,))
            print(f"Frontend ready in {frontend_seconds:.2f}s ({time.monotonic() - started:.2f}s since launcher).", flush=True)
            print("UniTrust is ready: http://127.0.0.1:8501\nPress Ctrl+C once to stop both services.", flush=True)
            while True:
                for process in processes:
                    if process.poll() is not None:
                        raise RuntimeError(f"Service PID {process.pid} exited with code {process.returncode}.")
                time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopping UniTrust...", flush=True)
        return 0
    except (OSError, RuntimeError, httpx.HTTPError) as exc:
        print(f"[FAIL] {exc}", flush=True)
        log_tail(backend_log)
        log_tail(frontend_log)
        return 1
    finally:
        for process in reversed(processes):
            try:
                stop_process(process)
            except (OSError, subprocess.SubprocessError) as exc:
                print(f"[WARN] Could not confirm stop of owned PID {process.pid}: {exc}", flush=True)
        if processes:
            print("Demo supervisor stopped. Re-run the same command to restart.", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend-timeout", type=float, default=180)
    parser.add_argument("--frontend-timeout", type=float, default=60)
    args = parser.parse_args()
    if args.backend_timeout <= 0 or args.frontend_timeout <= 0:
        parser.error("readiness timeouts must be positive")
    return run_demo(args.backend_timeout, args.frontend_timeout)


if __name__ == "__main__":
    raise SystemExit(main())
