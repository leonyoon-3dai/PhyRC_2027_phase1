"""Public-observation Codex CLI actor, isolated from the simulator and repository.

The controller owns this module. Only staged public inputs, a native Codex
executable, and a new private Codex home are mounted into the actor container.
An internal, isolated Docker bridge reaches a CONNECT proxy which permits only
the authentication/model origins below. No host ports are published.

Feature flags reduce tools but are not a proof of a tool-free model registry.
Any tool item in the event stream invalidates the returned decision. Docker is
the filesystem/network boundary; the controller must still validate actions.
"""
from __future__ import annotations

import hashlib
import ipaddress
import json
import math
import os
from pathlib import Path
import select
import shutil
import socket
import socketserver
import subprocess
import sys
import threading
import time
import uuid


ACTOR_IMAGE = "python:3.12-slim@sha256:4840d514c583a4d3d8cad3940e68dee6f0f6f3635c12fcd0a3d74c21a5b93a54"
SUPPORTED_CLI = "codex-cli 0.166.0"
MODEL_ORIGINS = frozenset({"chatgpt.com", "auth.openai.com", "api.openai.com"})
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
MAX_EVENT_BYTES = 16 * 1024 * 1024
# Codex 0.166.0 emits these nonfatal startup notices as item.error. They are
# accepted only before turn.started; every other error/tool item fails closed.
STARTUP_NOTICES = frozenset({
    "Code Mode is unavailable because code-mode host is disabled. Code mode will fail closed; enable `features.code_mode_host` and install `codex-code-mode-host`.",
    "Under-development features enabled: skip_host_skill_discovery. Under-development features are incomplete and may behave unpredictably. To suppress this warning, set `suppress_unstable_features_warning = true` in /codex/config.toml.",
})
DISABLED_FEATURES = (
    "shell_tool", "unified_exec", "unified_exec_tty", "shell_snapshot",
    "shell_snapshot_v2", "apps", "plugins", "plugin_discovery_prefetch",
    "plugin_sharing", "remote_plugin", "multi_agent", "multi_agent_v2",
    "browser_use", "browser_use_external", "browser_use_full_cdp_access",
    "computer_use", "image_generation", "in_app_browser", "hooks",
    "memories", "view_image", "code_mode", "code_mode_host", "skill_search",
    "skill_mcp_dependency_install", "goals", "sleep_tool", "tool_suggest",
    "workspace_dependencies", "daemon_auto_start", "request_permissions_tool",
    "default_mode_request_user_input", "unbounded_connection_retries",
)


class ActorError(RuntimeError):
    """A failed actor turn. Its output must never be dispatched as an action."""


def _json_loads(text: str):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON field")
            result[key] = value
        return result

    def constant(_):
        raise ValueError("non-finite JSON number")

    value = json.loads(text, object_pairs_hook=pairs, parse_constant=constant)

    def finite(item):
        if isinstance(item, float) and not math.isfinite(item):
            raise ValueError("non-finite JSON number")
        if isinstance(item, dict):
            for child in item.values():
                finite(child)
        elif isinstance(item, list):
            for child in item:
                finite(child)

    finite(value)
    return value


def _read_result(events: Path, response: Path, expected_session: str | None):
    """Accept only a completed response-only turn, never an embedded tool result."""
    if events.stat().st_size > MAX_EVENT_BYTES:
        raise ActorError("actor event log exceeded the limit")
    session = None
    usage = None
    completed = 0
    turn_started = False
    with events.open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            event = _json_loads(line)
            kind = event.get("type")
            if kind == "thread.started":
                value = str(uuid.UUID(event["thread_id"]))
                if session is not None and session != value:
                    raise ActorError("actor changed session within one turn")
                session = value
            elif kind == "turn.completed":
                completed += 1
                usage = event.get("usage", {})
            elif kind in {"error", "turn.failed"}:
                raise ActorError("Codex reported a failed turn; inspect the private trace")
            elif kind in {"item.started", "item.updated", "item.completed"}:
                item = event.get("item", {})
                item_kind = item.get("type")
                if (kind == "item.completed" and not turn_started and item_kind == "error"
                        and item.get("message") in STARTUP_NOTICES):
                    continue
                if item_kind not in {"agent_message", "reasoning"}:
                    raise ActorError("actor emitted a tool or unsupported item; action rejected")
            elif kind == "turn.started":
                if turn_started:
                    raise ActorError("actor started more than one turn")
                turn_started = True
            else:
                raise ActorError("actor emitted an unsupported event; action rejected")
    if completed != 1 or session is None:
        raise ActorError("actor did not produce one complete identified turn")
    if expected_session is not None and session != expected_session:
        raise ActorError("actor resumed a different session")
    if not isinstance(usage, dict) or any(
        type(v) is not int or v < 0 for v in usage.values()
    ):
        raise ActorError("invalid actor token usage")
    if not response.is_file() or response.stat().st_size > MAX_RESPONSE_BYTES:
        raise ActorError("actor response is missing or exceeds the limit")
    decision = _json_loads(response.read_text(encoding="utf-8"))
    if not isinstance(decision, dict):
        raise ActorError("actor response must be a JSON object")
    return decision, session, usage


def _native_binary() -> Path:
    executable = shutil.which("codex")
    if not executable:
        raise ActorError("Codex CLI is not installed")
    path = Path(executable).resolve()
    if path.suffix == ".js":
        path = (path.parent.parent / "node_modules/@openai/codex-linux-x64/vendor"
                / "x86_64-unknown-linux-musl/bin/codex")
    if not path.is_file():
        raise ActorError("the Linux x64 native Codex executable was not found")
    with path.open("rb") as stream:
        if stream.read(4) != b"\x7fELF":
            raise ActorError("actor requires the native Linux Codex executable")
    return path


def _clean_environment():
    # The Docker CLI uses the local socket. Do not inherit API/HF/GitHub tokens,
    # remote Docker endpoints, proxies, or user Docker credential helpers.
    return {"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "DOCKER_CONFIG": "/nonexistent-phyrc-actor-config", "LANG": "C.UTF-8"}


def _private_write(path: Path, text: str):
    with path.open("x", encoding="utf-8") as stream:
        os.chmod(path, 0o600)
        stream.write(text)


class Actor:
    """One episode's CLI session. ``root`` is private runtime storage, not a repo.

    ``invoke`` stages images by pixel-only PNG re-encoding and returns decision,
    session_id, wall_s, usage, model, effort and CLI version. Close explicitly or
    use a context manager. A failed turn poisons this actor; start a new episode
    instead of silently retrying with ambiguous action history.
    """

    def __init__(self, root: Path, model: str = "gpt-6-astra", effort: str = "ultra",
                 timeout_s: float = 600, *, auth_path: Path | None = None,
                 binary_path: Path | None = None):
        if model != "gpt-6-astra" or effort != "ultra":
            raise ValueError("this adapter is validated only for gpt-6-astra / ultra")
        if not math.isfinite(timeout_s) or timeout_s <= 0:
            raise ValueError("timeout_s must be finite and positive")
        self.root = Path(root).resolve()
        self.model, self.effort, self.timeout_s = model, effort, timeout_s
        self.session_id = None
        self.calls = 0
        self._closed = False
        self._failed = False
        self._lock = threading.Lock()
        self._network_created = False
        self._proxy_created = False
        self._active_container = None
        suffix = uuid.uuid4().hex[:16]
        self.network = "phyrc-actor-" + suffix
        self.proxy = self.network + "-egress"
        self.binary = Path(binary_path).resolve() if binary_path else _native_binary()
        self.public = self.root / "public"
        self.codex_home = self.root / "codex_home"
        self.events = self.root / "actor_events"
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(self.root, 0o700)
        for directory in (self.public, self.codex_home, self.events):
            directory.mkdir(mode=0o700, exist_ok=False)
        try:
            source = auth_path or Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "auth.json"
            source = Path(source)
            if not source.is_file() or source.stat().st_mode & 0o077:
                raise ActorError("Codex auth.json must exist with private permissions")
            shutil.copyfile(source, self.codex_home / "auth.json")
            os.chmod(self.codex_home / "auth.json", 0o600)
            version = subprocess.run([str(self.binary), "--version"], check=True,
                                     capture_output=True, text=True, timeout=15,
                                     env=_clean_environment()).stdout.strip()
            if version != SUPPORTED_CLI:
                raise ActorError("this adapter requires Codex CLI 0.166.0")
            self.cli_version = version
            self._provision()
        except BaseException:
            self.close()
            raise

    def _docker(self, arguments, *, timeout=30):
        result = subprocess.run(["docker", *arguments], capture_output=True,
                                text=True, timeout=timeout, env=_clean_environment())
        if result.returncode:
            # Docker/CLI messages may contain paths or credentials: never echo.
            raise ActorError("Docker actor setup failed at " + arguments[0])
        return result.stdout.strip()

    @staticmethod
    def _limits():
        return ["--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges",
                "--pids-limit=96", "--memory=2g", "--cpus=2",
                "--user", f"{os.getuid()}:{os.getgid()}",
                "--tmpfs", "/tmp:rw,nosuid,nodev,noexec,size=134217728,mode=1777"]

    def _provision(self):
        self._docker(["image", "inspect", ACTOR_IMAGE])
        self._docker(["network", "create", "--internal", "--driver=bridge",
                      "--opt", "com.docker.network.bridge.gateway_mode_ipv4=isolated",
                      self.network])
        self._network_created = True
        info = json.loads(self._docker(["network", "inspect", self.network]))[0]
        if not info.get("Internal") or info.get("Options", {}).get(
            "com.docker.network.bridge.gateway_mode_ipv4") != "isolated":
            raise ActorError("Docker did not create an isolated internal network")
        self._docker(["create", "--name", self.proxy, *self._limits(),
                      "--network", self.network, "--network-alias", "model-egress",
                      "--mount", f"type=bind,src={Path(__file__).resolve()},dst=/proxy.py,readonly",
                      ACTOR_IMAGE, "python", "-I", "/proxy.py", "--egress-proxy"])
        self._proxy_created = True
        self._docker(["network", "connect", "--gw-priority", "1", "bridge", self.proxy])
        self._docker(["start", self.proxy])
        # Readiness uses the container's own loopback; no host port is opened.
        ready = ("import socket,time\n"
                 "for _ in range(50):\n"
                 " try:\n  s=socket.create_connection(('127.0.0.1',8080),.1);s.close();break\n"
                 " except OSError: time.sleep(.1)\n"
                 "else: raise SystemExit(1)\n")
        self._docker(["exec", self.proxy, "python", "-c", ready], timeout=15)

    def _cli(self, schema_name: str, response_name: str, image_names: list[str]):
        command = ["codex", "exec", "-s", "read-only", "-C", "/public"]
        if self.session_id is not None:
            command.append("resume")
        command.extend(["--ignore-user-config", "--ignore-rules", "--strict-config",
                        "--skip-git-repo-check", "--json", "-m", self.model,
                        "--output-schema", "/public/" + schema_name,
                        "--output-last-message", "/codex/" + response_name])
        config = {
            "model_reasoning_effort": self.effort,
            "approval_policy": "never", "web_search": "disabled",
            "cli_auth_credentials_store": "file", "forced_login_method": "chatgpt",
            "project_doc_max_bytes": 0, "skills.bundled.enabled": False,
            "skills.include_instructions": False, "agents.enabled": False,
            "features.skip_host_skill_discovery": True,
            "suppress_unstable_features_warning": True,
            "developer_instructions": "Use only the supplied public observations. Return the requested JSON decision without invoking any tools.",
        }
        for name, value in config.items():
            command.extend(["-c", name + "=" + json.dumps(value)])
        for feature in DISABLED_FEATURES:
            command.extend(["--disable", feature])
        for name in image_names:
            command.extend(["-i", "/public/" + name])
        if self.session_id is not None:
            command.append(self.session_id)
        command.append("-")
        return command

    def _container_command(self, name: str, request_dir: Path, cli: list[str]):
        return ["docker", "run", "--rm", "-i", "--name", name, *self._limits(),
                "--network", self.network, "--workdir", "/public",
                "--env", "CODEX_HOME=/codex", "--env", "HOME=/tmp/actor-home",
                "--env", "HTTPS_PROXY=http://model-egress:8080",
                "--env", "HTTP_PROXY=http://model-egress:8080", "--env", "NO_PROXY=",
                "--mount", f"type=bind,src={self.binary},dst=/usr/local/bin/codex,readonly",
                "--mount", f"type=bind,src={request_dir},dst=/public,readonly",
                "--mount", f"type=bind,src={self.codex_home},dst=/codex",
                ACTOR_IMAGE, *cli]

    def invoke(self, prompt: str, images: list[Path], schema: dict) -> dict:
        if not self._lock.acquire(blocking=False):
            raise ActorError("one actor may not execute concurrent decisions")
        started = time.perf_counter()
        try:
            if self._closed or self._failed:
                raise ActorError("actor is closed or has a failed turn")
            if not isinstance(prompt, str) or not prompt or len(prompt.encode()) > 256 * 1024:
                raise ValueError("prompt must be nonempty and at most 256 KiB")
            if not 1 <= len(images) <= 16:
                raise ValueError("one to sixteen designated public camera images required")
            from PIL import Image

            turn = f"{self.calls:06d}"
            request_dir = self.public / turn
            request_dir.mkdir(mode=0o700)
            _private_write(request_dir / "schema.json", json.dumps(schema, allow_nan=False))
            _private_write(request_dir / "prompt.txt", prompt)
            image_names = []
            for index, path in enumerate(images):
                name = f"camera-{index:02d}.png"
                with Image.open(path) as source:
                    if source.width * source.height > 4096 * 4096:
                        raise ValueError("public camera image exceeds size limit")
                    # A new image discards PNG text/EXIF and filenames entirely.
                    rgb = source.convert("RGB")
                    clean = Image.frombytes("RGB", rgb.size, rgb.tobytes())
                    clean.save(request_dir / name, format="PNG")
                image_names.append(name)
            response_name = "decision-" + turn + ".json"
            response = self.codex_home / response_name
            if response.exists():
                raise ActorError("a stale response file already exists")
            # Resume can refer to historical local-image paths. Keep immutable
            # turn-specific paths mounted for the lifetime of this episode.
            cli = self._cli(turn + "/schema.json", response_name,
                            [turn + "/" + name for name in image_names])
            name = self.network + "-" + turn
            command = self._container_command(name, self.public, cli)
            self._active_container = name
            event_path = self.events / (turn + ".jsonl")
            error_path = self.events / (turn + ".stderr")
            with event_path.open("xb") as event_log, error_path.open("xb") as error_log:
                process = subprocess.Popen(command, stdin=subprocess.PIPE,
                                           stdout=event_log, stderr=error_log,
                                           env=_clean_environment())
                try:
                    process.communicate(prompt.encode(), timeout=self.timeout_s)
                except subprocess.TimeoutExpired:
                    cleanup_failed = False
                    try:
                        self._remove_container(name)
                        self._active_container = None
                    except Exception:
                        cleanup_failed = True
                    finally:
                        process.kill()
                        process.wait(timeout=10)
                    suffix = "; container cleanup pending" if cleanup_failed else ""
                    raise ActorError("Codex inference timed out; no action returned" + suffix) from None
                except BaseException:
                    try:
                        self._remove_container(name)
                        self._active_container = None
                    except Exception:
                        pass  # close() retries; preserve the interrupted turn's cause.
                    finally:
                        process.kill()
                        process.wait(timeout=10)
                    raise
            self._active_container = None
            if process.returncode:
                raise ActorError("Codex CLI failed; inspect the private actor trace")
            decision, session, usage = _read_result(event_path, response, self.session_id)
            self.session_id = session
            self.calls += 1
            return {"decision": decision, "session_id": session,
                    "wall_s": time.perf_counter() - started, "usage": usage,
                    "model": self.model, "effort": self.effort,
                    "cli_version": self.cli_version,
                    "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest()}
        except BaseException:
            self._failed = True
            if self._active_container is not None:
                try:
                    self._remove_container(self._active_container)
                except Exception:
                    # Keep the resource identity for close() to retry. The
                    # original failed turn remains unusable in either case.
                    pass
                else:
                    self._active_container = None
            raise
        finally:
            self._lock.release()

    def _remove_container(self, name):
        try:
            result = subprocess.run(["docker", "rm", "-f", name], capture_output=True,
                                    text=True, timeout=30, env=_clean_environment())
        except (OSError, subprocess.TimeoutExpired):
            raise ActorError("actor container cleanup failed") from None
        if result.returncode and "no such container" not in (result.stderr or "").lower():
            raise ActorError("actor container cleanup failed")

    def close(self):
        if self._closed:
            return
        # Even if cleanup needs a retry, this actor must never accept more turns
        # after credentials or part of its network have been removed.
        self._failed = True
        errors = []
        completed = False
        try:
            if self._active_container is not None:
                try:
                    self._remove_container(self._active_container)
                except Exception:
                    errors.append("active_container")
                else:
                    self._active_container = None
            if self._proxy_created:
                try:
                    self._remove_container(self.proxy)
                except Exception:
                    errors.append("proxy")
                else:
                    self._proxy_created = False
            if self._network_created:
                try:
                    result = subprocess.run(["docker", "network", "rm", self.network],
                                            capture_output=True, text=True, timeout=30,
                                            env=_clean_environment())
                    message = (result.stderr or "").lower()
                    absent = "no such network" in message or (
                        "network " + self.network.lower() + " not found") in message
                    if result.returncode and not absent:
                        raise ActorError("actor network cleanup failed")
                except Exception:
                    errors.append("network")
                else:
                    self._network_created = False
            completed = True
        finally:
            # Credentials must not remain in retained evidence when any Docker
            # cleanup operation fails. Resource flags permit a later retry.
            try:
                (self.codex_home / "auth.json").unlink(missing_ok=True)
            except OSError:
                errors.append("credentials")
            self._closed = completed and not errors
        if errors:
            raise ActorError("actor cleanup incomplete; retry close()")

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


def _proxy_destination(target: str):
    """Exact HTTPS authority allowlist, before DNS; never relay local IPs."""
    if target.count(":") != 1:
        raise ValueError("invalid CONNECT authority")
    host, port = target.split(":")
    if host not in MODEL_ORIGINS or port != "443":
        raise ValueError("origin not permitted")
    addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise ValueError("non-public model origin")
    return addresses


class _ConnectHandler(socketserver.BaseRequestHandler):
    def handle(self):
        self.request.settimeout(15)
        raw = b""
        while b"\r\n\r\n" not in raw and len(raw) <= 16384:
            chunk = self.request.recv(4096)
            if not chunk:
                return
            raw += chunk
        try:
            header, extra = raw.split(b"\r\n\r\n", 1)
            method, target, version = header.split(b"\r\n", 1)[0].decode("ascii").split(" ")
            if method != "CONNECT" or version not in {"HTTP/1.0", "HTTP/1.1"} or extra:
                raise ValueError("CONNECT required")
            addresses = _proxy_destination(target)
        except (ValueError, UnicodeError, OSError):
            self.request.sendall(b"HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n")
            return
        upstream = None
        for family, socktype, proto, _, address in addresses:
            candidate = socket.socket(family, socktype, proto)
            candidate.settimeout(20)
            try:
                candidate.connect(address)
                upstream = candidate
                break
            except OSError:
                candidate.close()
        if upstream is None:
            self.request.sendall(b"HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\n\r\n")
            return
        with upstream:
            self.request.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            self.request.settimeout(30)
            upstream.settimeout(30)
            deadline = time.monotonic() + 1800
            while time.monotonic() < deadline:
                readable, _, _ = select.select([self.request, upstream], [], [], 30)
                for source in readable:
                    data = source.recv(65536)
                    if not data:
                        return
                    (upstream if source is self.request else self.request).sendall(data)


def _serve_proxy():
    class Server(socketserver.ThreadingTCPServer):
        allow_reuse_address = True
        daemon_threads = True

        def handle_error(self, *_):
            # Deliberately do not log requests, headers, tokens or destinations.
            pass

    with Server(("0.0.0.0", 8080), _ConnectHandler) as server:
        server.serve_forever()


if __name__ == "__main__":
    if sys.argv[1:] == ["--egress-proxy"]:
        _serve_proxy()
    else:
        raise SystemExit("Use Actor from the public-observation controller")
