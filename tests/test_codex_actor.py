"""CPU tests for the actor boundary. These never call a model or Docker."""
import json
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch
import uuid

from participant.collection.codex_actor import (
    Actor, ActorError, STARTUP_NOTICES, _json_loads, _native_binary, _proxy_destination, _read_result,
)


class ActorBoundaryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.session = str(uuid.uuid4())

    def test_npm_launcher_resolves_sibling_native_package(self):
        scope = self.root / 'node_modules/@openai'
        launcher = scope / 'codex/bin/codex.js'
        launcher.parent.mkdir(parents=True)
        launcher.write_text('// npm launcher')
        native = scope / 'codex-linux-x64/vendor/x86_64-unknown-linux-musl/bin/codex'
        native.parent.mkdir(parents=True)
        native.write_bytes(b'\x7fELFfixture')
        link = self.root / 'codex'
        link.symlink_to(launcher)
        with patch('participant.collection.codex_actor.shutil.which', return_value=str(link)):
            self.assertEqual(_native_binary(), native)
            native.write_bytes(b'not an executable')
            with self.assertRaises(ActorError):
                _native_binary()

    def write_result(self, *, item=None, session=None, response=None, complete=True):
        events = [
            {"type": "thread.started", "thread_id": session or self.session},
            {"type": "turn.started"},
            {"type": "item.completed", "item": item or {
                "type": "agent_message", "text": "This event is not the action."}},
        ]
        if complete:
            events.append({"type": "turn.completed", "usage": {
                "input_tokens": 12, "cached_input_tokens": 4, "output_tokens": 3}})
        event_path = self.root / "events.jsonl"
        event_path.write_text("\n".join(map(json.dumps, events)))
        response_path = self.root / "response.json"
        response_path.write_text(response or '{"tool":"stop"}')
        return event_path, response_path

    def test_completed_turn_uses_output_file_and_explicit_session(self):
        decision, session, usage = _read_result(*self.write_result(), self.session)
        self.assertEqual(decision, {"tool": "stop"})
        self.assertEqual(session, self.session)
        self.assertEqual(usage["input_tokens"], 12)

    def test_any_tool_or_unknown_item_rejects_otherwise_valid_decision(self):
        for kind in ("command_execution", "file_change", "mcp_tool_call",
                     "web_search", "unknown_future_tool"):
            with self.subTest(kind=kind), self.assertRaises(ActorError):
                _read_result(*self.write_result(item={"type": kind}), None)

    def test_missing_completion_and_wrong_session_are_rejected(self):
        with self.assertRaises(ActorError):
            _read_result(*self.write_result(complete=False), None)
        with self.assertRaises(ActorError):
            _read_result(*self.write_result(), str(uuid.uuid4()))

    def test_only_exact_nonfatal_notices_before_turn_start_are_accepted(self):
        event_path, response_path = self.write_result()
        events = [json.loads(line) for line in event_path.read_text().splitlines()]
        notices = [{"type": "item.completed", "item": {"type": "error", "message": text}}
                   for text in STARTUP_NOTICES]
        accepted = [events[0], *notices, *events[1:]]
        event_path.write_text("\n".join(map(json.dumps, accepted)))
        _read_result(event_path, response_path, None)
        for rejected in (
            [*events[:2], *notices, *events[2:]],
            [events[0], {"type": "item.completed", "item": {
                "type": "error", "message": "Authentication failed"}}, *events[1:]],
        ):
            event_path.write_text("\n".join(map(json.dumps, rejected)))
            with self.assertRaises(ActorError):
                _read_result(event_path, response_path, None)

    def test_ambiguous_or_nonfinite_json_is_rejected(self):
        for text in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}',
                     '{"a":1e999}', '{"a":[-1e999]}'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                _json_loads(text)

    def test_proxy_rejects_non_model_origins_without_dns(self):
        with patch("participant.collection.codex_actor.socket.getaddrinfo") as dns:
            for target in ("localhost:8888", "127.0.0.1:443", "chatgpt.com:8888",
                           "chatgpt.com.evil.test:443", "CHATGPT.COM:443",
                           "auth.openai.com.:443", "[::1]:443"):
                with self.subTest(target=target), self.assertRaises(ValueError):
                    _proxy_destination(target)
            dns.assert_not_called()

    def test_proxy_rejects_rebinding_to_private_address(self):
        for address in ("127.0.0.1", "169.254.169.254", "172.18.0.1", "::1"):
            answer = [(2, 1, 6, "", (address, 443))]
            with patch("participant.collection.codex_actor.socket.getaddrinfo", return_value=answer):
                with self.subTest(address=address), self.assertRaises(ValueError):
                    _proxy_destination("chatgpt.com:443")

    def test_resume_keeps_parent_options_and_exact_session(self):
        actor = object.__new__(Actor)
        actor.model, actor.effort = "gpt-6-astra", "ultra"
        actor.session_id = self.session
        command = actor._cli("schema.json", "reply.json", ["camera-00.png", "camera-01.png"])
        self.assertLess(command.index("-s"), command.index("resume"))
        self.assertLess(command.index("-C"), command.index("resume"))
        self.assertEqual(command[-2:], [self.session, "-"])
        self.assertNotIn("--last", command)
        self.assertNotIn("--ephemeral", command)
        self.assertEqual(command.count("-i"), 2)

    def test_container_mounts_only_explicit_public_directory_and_own_home(self):
        actor = object.__new__(Actor)
        actor.network = "test-isolated-network"
        actor.binary = Path("/native/codex")
        actor.codex_home = self.root / "runtime/codex_home"
        request_dir = self.root / "runtime/public/000000"
        command = actor._container_command("test-actor", request_dir, ["codex", "--version"])
        mounts = [command[i + 1] for i, arg in enumerate(command) if arg == "--mount"]
        self.assertEqual(len(mounts), 3)
        self.assertTrue(any(f"src={request_dir},dst=/public,readonly" in m for m in mounts))
        self.assertFalse(any(f"src={self.root}," in m for m in mounts))
        self.assertNotIn("--privileged", command)
        self.assertNotIn("--gpus", command)
        self.assertNotIn("--publish", command)
        self.assertIn("--read-only", command)
        self.assertIn("--cap-drop=ALL", command)

    def test_repeated_turns_keep_original_pixels_and_strip_metadata(self):
        from PIL import Image
        from PIL.PngImagePlugin import PngInfo

        actor = object.__new__(Actor)
        actor.model, actor.effort = "gpt-6-astra", "ultra"
        actor.cli_version, actor.timeout_s = "fixture", 10
        actor.session_id, actor.calls = None, 0
        actor._closed = actor._failed = False
        actor._active_container = None
        actor._lock = threading.Lock()
        actor.network, actor.binary = "fixture-network", Path("/native/codex")
        actor.public, actor.codex_home, actor.events = [self.root / name for name in
                                                       ("public", "home", "events")]
        for directory in (actor.public, actor.codex_home, actor.events):
            directory.mkdir()
        incoming = self.root / "mutable-input.png"
        metadata = PngInfo()
        metadata.add_text("not_public", "metadata-canary")
        commands = []
        session = self.session

        class Process:
            returncode = 0

            def __init__(self, command, *, stdout, **_):
                commands.append(command)
                self.stdout = stdout
                self.response_name = Path(command[command.index("--output-last-message") + 1]).name

            def communicate(self, payload, timeout):
                self.stdout.write((json.dumps({"type": "thread.started", "thread_id": session}) + "\n" +
                                   json.dumps({"type": "turn.completed", "usage": {"input_tokens": 1}}) + "\n").encode())
                (actor.codex_home / self.response_name).write_text('{"tool":"stop"}')

        with patch("participant.collection.codex_actor.subprocess.Popen", Process):
            Image.new("RGB", (4, 4), "red").save(incoming, pnginfo=metadata)
            first = actor.invoke("public first observation", [incoming], {"type": "object"})
            Image.new("RGB", (4, 4), "blue").save(incoming, pnginfo=metadata)
            second = actor.invoke("public second observation", [incoming], {"type": "object"})
        self.assertEqual(first["session_id"], second["session_id"])
        for result in (first, second):
            phases = result["phase_wall_s"]
            self.assertTrue(phases["completed"])
            measured = [phases[key] for key in
                        ("staging_wall_s", "process_wall_s", "result_parse_wall_s")]
            self.assertTrue(all(value >= 0 for value in measured))
            self.assertLessEqual(sum(measured), result["wall_s"])
        self.assertNotIn("resume", commands[0])
        self.assertIn("resume", commands[1])
        self.assertIn("/public/000000/camera-00.png", commands[0])
        self.assertIn("/public/000001/camera-00.png", commands[1])
        with Image.open(actor.public / "000000/camera-00.png") as image:
            self.assertEqual(image.getpixel((0, 0)), (255, 0, 0))
            self.assertNotIn("not_public", image.info)
        with Image.open(actor.public / "000001/camera-00.png") as image:
            self.assertEqual(image.getpixel((0, 0)), (0, 0, 255))
            self.assertNotIn("not_public", image.info)

    def cleanup_actor(self):
        actor = object.__new__(Actor)
        actor._closed = actor._failed = False
        actor._active_container = "fixture-active"
        actor._proxy_created = actor._network_created = True
        actor.proxy, actor.network = "fixture-proxy", "fixture-network"
        actor.codex_home = self.root / "cleanup-home"
        actor.codex_home.mkdir()
        (actor.codex_home / "auth.json").write_text("fixture-only")
        return actor

    def test_cleanup_timeout_removes_credentials_and_retries_only_remaining_resources(self):
        actor = self.cleanup_actor()
        calls = []

        def first(command, **_):
            calls.append(command)
            if command[-1] == actor._active_container:
                raise subprocess.TimeoutExpired(command, 30)
            if command[1:3] == ["network", "rm"]:
                return subprocess.CompletedProcess(command, 1, "", "network has active endpoints")
            return subprocess.CompletedProcess(command, 0, "", "")

        with patch("participant.collection.codex_actor.subprocess.run", side_effect=first):
            with self.assertRaisesRegex(ActorError, "cleanup incomplete"):
                actor.close()
        self.assertEqual([c[-1] for c in calls], ["fixture-active", "fixture-proxy", "fixture-network"])
        self.assertFalse((actor.codex_home / "auth.json").exists())
        self.assertFalse(actor._closed)
        self.assertTrue(actor._failed)
        self.assertEqual(actor._active_container, "fixture-active")
        self.assertFalse(actor._proxy_created)
        self.assertTrue(actor._network_created)
        calls.clear()

        def retry(command, **_):
            calls.append(command)
            return subprocess.CompletedProcess(command, 0, "", "")

        with patch("participant.collection.codex_actor.subprocess.run", side_effect=retry):
            actor.close()
            actor.close()
        self.assertEqual([c[-1] for c in calls], ["fixture-active", "fixture-network"])
        self.assertTrue(actor._closed)
        self.assertIsNone(actor._active_container)
        self.assertFalse(actor._network_created)

    def test_remove_container_tolerates_missing_resource_but_rejects_daemon_errors(self):
        actor = object.__new__(Actor)
        for message in ("Error response from daemon: No such container: fixture", "permission denied"):
            with self.subTest(message=message), patch(
                "participant.collection.codex_actor.subprocess.run",
                return_value=subprocess.CompletedProcess([], 1, "", message),
            ):
                if "No such container" in message:
                    actor._remove_container("fixture")
                else:
                    with self.assertRaisesRegex(ActorError, "container cleanup failed"):
                        actor._remove_container("fixture")

    def test_cleanup_network_timeout_still_removes_auth_and_retains_retry_state(self):
        actor = self.cleanup_actor()
        actor._active_container = None
        actor._proxy_created = False
        with patch("participant.collection.codex_actor.subprocess.run",
                   side_effect=subprocess.TimeoutExpired(["docker", "network", "rm"], 30)):
            with self.assertRaises(ActorError):
                actor.close()
        self.assertFalse((actor.codex_home / "auth.json").exists())
        self.assertTrue(actor._network_created)
        self.assertFalse(actor._closed)

    def test_inference_timeout_stops_local_cli_even_when_container_cleanup_fails(self):
        from PIL import Image

        actor = self.cleanup_actor()
        actor._active_container = None
        actor.model, actor.effort, actor.timeout_s = "gpt-6-astra", "ultra", 10
        actor.session_id, actor.calls = None, 0
        actor._lock = threading.Lock()
        actor.public, actor.events = self.root / "public", self.root / "events"
        actor.public.mkdir(); actor.events.mkdir()
        actor.binary = Path("/native/codex")
        incoming = self.root / "input.png"
        Image.new("RGB", (4, 4), "red").save(incoming)
        calls = []

        class Process:
            def __init__(self, *_args, **_kwargs):
                pass
            def communicate(self, payload, timeout):
                raise subprocess.TimeoutExpired(["docker", "run"], timeout)
            def kill(self):
                calls.append("kill")
            def wait(self, timeout):
                calls.append("wait")
                return 0

        with patch("participant.collection.codex_actor.subprocess.Popen", Process), \
             patch.object(actor, "_remove_container", side_effect=ActorError("cleanup failed")):
            with self.assertRaisesRegex(ActorError, "inference timed out.*cleanup pending"):
                actor.invoke("public input", [incoming], {"type": "object"})
        self.assertEqual(calls, ["kill", "wait"])
        self.assertTrue(actor._failed)
        self.assertIsNotNone(actor._active_container)
        self.assertTrue(actor._lock.acquire(blocking=False))
        actor._lock.release()


if __name__ == "__main__":
    unittest.main()
