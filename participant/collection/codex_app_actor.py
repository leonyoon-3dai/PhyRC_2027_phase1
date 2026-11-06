"""Experimental persistent stdio actor; not selected by the collection runner.

Protocol: https://learn.chatgpt.com/docs/app-server, CLI 0.166.0 schemas.
Inherits only the existing actor's provisioning/isolation/cleanup. A single
private app-server and explicit thread persist across turns. No automatic
restart/resume follows failure, since the action history would be ambiguous.
Raw RPC logs are private evidence and may contain reasoning; never publish them.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import select
import subprocess
import time
import uuid

from participant.collection.codex_actor import (
    Actor, ActorError, MAX_EVENT_BYTES, MAX_RESPONSE_BYTES, STARTUP_NOTICES,
    _clean_environment, _json_loads, _private_write,
)

# Exact 0.166.0 informational notice observed before any thread/turn. The
# documented bundled-helper fallback does not change our outer Docker boundary.
# This does not whitelist inability to create namespaces or any config failure.
BUNDLED_BWRAP_NOTICE = (
    'Codex could not find bubblewrap on PATH. Install bubblewrap with your OS '
    'package manager. See the sandbox prerequisites: '
    'https://developers.openai.com/codex/concepts/sandboxing#prerequisites. '
    'Codex will use the bundled bubblewrap in the meantime.'
)


def _identifier(value):
    try:
        return str(uuid.UUID(value))
    except (ValueError, TypeError, AttributeError):
        raise ActorError('invalid app-server identifier') from None


def validate_schema(value, schema, *, check_only=False):
    """Strict local subset sufficient for the public action and probe schemas.

    Unknown schema keywords fail before a model call. This is deliberately not
    a general JSON Schema implementation; it never silently ignores a rule.
    """
    if not isinstance(schema, dict):
        raise ActorError('unsupported output schema')
    kind = schema.get('type')
    types = {'object': dict, 'array': list, 'string': str, 'integer': int,
             'boolean': bool, 'null': type(None)}
    if kind not in {*types, 'number'}:
        raise ActorError('unsupported output schema type')
    allowed = {'type', 'enum', 'description', 'title'} | {
        'object': {'properties', 'required', 'additionalProperties'},
        'array': {'items', 'minItems', 'maxItems'},
        'string': {'minLength', 'maxLength'},
        'integer': {'minimum', 'maximum'}, 'number': {'minimum', 'maximum'},
    }.get(kind, set())
    if set(schema) - allowed:
        raise ActorError('unsupported output schema constraint')
    for key in ('minItems', 'maxItems', 'minLength', 'maxLength'):
        if key in schema and (type(schema[key]) is not int or schema[key] < 0):
            raise ActorError('invalid output schema bound')
    for key in ('minimum', 'maximum'):
        if key in schema and (type(schema[key]) not in (int, float) or not math.isfinite(schema[key])):
            raise ActorError('invalid output schema bound')
    if 'enum' in schema and (not isinstance(schema['enum'], list) or not schema['enum']):
        raise ActorError('invalid output schema enum')
    if kind == 'object':
        properties = schema.get('properties', {})
        required = schema.get('required', [])
        if (not isinstance(properties, dict) or not isinstance(required, list)
                or any(not isinstance(k, str) for k in required)
                or set(required) - set(properties)
                or schema.get('additionalProperties') is not False):
            raise ActorError('object schema must be closed')
        for item in properties.values():
            validate_schema(None, item, check_only=True)
    if kind == 'array':
        validate_schema(None, schema.get('items'), check_only=True)
    if check_only:
        return
    if (kind == 'number' and (type(value) not in (int, float) or not math.isfinite(value))
            or kind != 'number' and type(value) is not types[kind]):
        raise ActorError('response does not match output schema')
    if 'enum' in schema and not any(type(value) is type(v) and value == v for v in schema['enum']):
        raise ActorError('response does not match output enum')
    if kind == 'object':
        if set(schema.get('required', [])) - set(value) or set(value) - set(schema['properties']):
            raise ActorError('response object fields do not match schema')
        for key, item in value.items():
            validate_schema(item, schema['properties'][key])
    elif kind == 'array':
        if not schema.get('minItems', 0) <= len(value) <= schema.get('maxItems', math.inf):
            raise ActorError('response array length does not match schema')
        for item in value:
            validate_schema(item, schema['items'])
    elif kind == 'string':
        if not schema.get('minLength', 0) <= len(value) <= schema.get('maxLength', math.inf):
            raise ActorError('response string length does not match schema')
    elif kind in ('number', 'integer'):
        if not schema.get('minimum', -math.inf) <= value <= schema.get('maximum', math.inf):
            raise ActorError('response number does not match schema')


def normalize_usage(value):
    names = {'inputTokens': 'input_tokens', 'cachedInputTokens': 'cached_input_tokens',
             'cacheWriteInputTokens': 'cache_write_input_tokens',
             'outputTokens': 'output_tokens', 'reasoningOutputTokens': 'reasoning_output_tokens',
             'totalTokens': 'total_tokens'}
    if (not isinstance(value, dict) or set(value) - set(names)
            or set(names) - {'cacheWriteInputTokens'} - set(value)
            or any(type(v) is not int or v < 0 for v in value.values())):
        raise ActorError('invalid app-server token usage')
    return {target: value.get(source, 0) for source, target in names.items()}


class TurnResult:
    """Allowlisted event reducer: tool items and unsupported events fail closed."""
    DELTAS = {'item/agentMessage/delta', 'item/reasoning/summaryTextDelta',
              'item/reasoning/summaryPartAdded', 'item/reasoning/textDelta'}

    def __init__(self, thread_id):
        self.thread_id = thread_id
        self.turn_id = None
        self.completed = False
        self.started = False
        self.messages = {}
        self.usage_total = self.usage_last = None

    def turn(self, turn):
        identity = _identifier(turn.get('id'))
        if self.turn_id is not None and identity != self.turn_id:
            raise ActorError('app-server changed turn')
        self.turn_id = identity
        if turn.get('status') not in ('inProgress', 'completed') or turn.get('error'):
            raise ActorError('app-server turn failed or was interrupted')
        for item in turn.get('items', []):
            self.item(item, completed=turn.get('status') == 'completed')

    def item(self, item, *, completed):
        kind = item.get('type')
        if kind not in ('userMessage', 'agentMessage', 'reasoning'):
            raise ActorError('actor emitted a tool or unsupported item')
        if kind == 'agentMessage' and completed:
            if item.get('phase') not in (None, 'final_answer', 'commentary', 'partial_answer'):
                raise ActorError('unsupported agent message phase')
            if item.get('phase') in (None, 'final_answer'):
                text = item.get('text')
                if not isinstance(text, str) or len(text.encode()) > MAX_RESPONSE_BYTES:
                    raise ActorError('invalid final app-server message')
                previous = self.messages.get(item['id'])
                if previous is not None and previous != text:
                    raise ActorError('app-server changed a completed message')
                self.messages[item['id']] = text

    def event(self, method, params):
        if params.get('threadId') != self.thread_id:
            raise ActorError('app-server event has a different thread')
        if method in ('turn/started', 'turn/completed'):
            self.turn(params['turn'])
            if method == 'turn/started':
                if self.started:
                    raise ActorError('app-server started a second turn')
                self.started = True
            if method == 'turn/completed':
                if self.completed or params['turn'].get('status') != 'completed':
                    raise ActorError('invalid app-server completion')
                self.completed = True
            return
        identity = _identifier(params.get('turnId'))
        if self.turn_id is not None and identity != self.turn_id:
            raise ActorError('app-server event has a different turn')
        self.turn_id = identity
        if method in ('item/started', 'item/completed'):
            self.item(params['item'], completed=method == 'item/completed')
        elif method == 'thread/tokenUsage/updated':
            self.usage_total = normalize_usage(params['tokenUsage']['total'])
            self.usage_last = normalize_usage(params['tokenUsage']['last'])
        elif method == 'turn/moderationMetadata':
            # 0.166.0 generated protocol schema: opaque diagnostic metadata,
            # never an action or tool permission. Keep it only in private RPC
            # evidence; a blocked result cannot authorize a returned action.
            metadata = params.get('metadata')
            def blocked(value):
                if isinstance(value, dict):
                    return value.get('is_blocked') is True or any(blocked(v) for v in value.values())
                return isinstance(value, list) and any(blocked(v) for v in value)
            if (not isinstance(metadata, dict) or metadata.get('tool_call')
                    or metadata.get('tool_response') or blocked(metadata)):
                raise ActorError('app-server moderation or tool metadata rejects the turn')
        elif method not in self.DELTAS:
            raise ActorError('unsupported app-server turn notification')

    def result(self, schema):
        if not self.started or not self.completed or len(self.messages) != 1 or self.usage_total is None:
            raise ActorError('missing final message, completion, or usage')
        decision = _json_loads(next(iter(self.messages.values())))
        if not isinstance(decision, dict):
            raise ActorError('app-server decision must be a JSON object')
        validate_schema(decision, schema)
        return decision


class AppActor(Actor):
    """Experimental drop-in invoke interface, with persistent stdio transport.

    Constructor provisions the same private containers as Actor, but starts no
    model turn. invoke is the only model-call path. Keep root coordination for
    both construction and actual probes; this class is not enabled by default.
    """
    def __init__(self, *args, **kwargs):
        self._process = self._rpc_log = self._stderr_log = None
        self._buffer = bytearray()
        self._request_id = 0
        self._event_bytes = 0
        self._turn = None
        self._announced_thread = None
        self._usage_total = {}
        started = time.perf_counter()
        super().__init__(*args, **kwargs)
        self.provision_wall_s = time.perf_counter() - started
        try:
            self._start_server()
        except BaseException:
            self.close()
            raise

    def _app_command(self):
        # Reuse precisely the existing feature/config values, not exec-only
        # flags that app-server does not support. CODEX_HOME is a new directory
        # containing only the private auth copy; no host user config/rules are
        # mounted. /public has only sanitized images/prompts/schema files.
        parent = Actor._cli(self, 'unused-schema.json', 'unused-response.json', [])
        command = ['codex', 'app-server', '--listen', 'stdio://', '--strict-config']
        for i, value in enumerate(parent[:-1]):
            if value in ('-c', '--disable'):
                command.extend([value, parent[i + 1]])
        command.extend(['-c', 'model=' + json.dumps(self.model),
                        '-c', 'sandbox_mode="read-only"'])
        return command

    def _start_server(self):
        started = time.perf_counter()
        self._active_container = self.network + '-app'
        self._rpc_log = (self.events / 'app-server-rpc.jsonl').open('xb')
        self._stderr_log = (self.events / 'app-server.stderr').open('xb')
        os.chmod(self.events / 'app-server-rpc.jsonl', 0o600)
        os.chmod(self.events / 'app-server.stderr', 0o600)
        command = self._container_command(self._active_container, self.public, self._app_command())
        self._process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                         stderr=self._stderr_log, env=_clean_environment())
        os.set_blocking(self._process.stdin.fileno(), False)
        deadline = time.monotonic() + min(self.timeout_s, 60)
        self._rpc('initialize', {'clientInfo': {'name': 'phyrc_public_actor_probe',
                    'version': '0.1.0'}, 'capabilities': {'experimentalApi': True}}, deadline)
        self._send({'method': 'initialized', 'params': {}}, deadline)
        result = self._rpc('thread/start', {
            'model': self.model, 'cwd': '/public', 'approvalPolicy': 'never',
            'sandbox': 'read-only', 'ephemeral': False, 'dynamicTools': [],
            'allowProviderModelFallback': False, 'experimentalRawEvents': False,
            'config': {'model_reasoning_effort': self.effort},
            'developerInstructions': 'Use only supplied public observations. Return the requested JSON without tools.',
        }, deadline)
        self.session_id = _identifier(result['thread']['id'])
        if (self._announced_thread not in (None, self.session_id)
                or result.get('model') != self.model
                or result.get('reasoningEffort') != self.effort
                or result.get('approvalPolicy') != 'never'
                or result.get('sandbox', {}).get('type') != 'readOnly'
                or result.get('instructionSources')):
            raise ActorError('app-server did not confirm the requested isolated configuration')
        self.startup_wall_s = time.perf_counter() - started

    def _send(self, value, deadline):
        data = (json.dumps(value, allow_nan=False) + '\n').encode()
        if len(data) > MAX_EVENT_BYTES:
            raise ActorError('app-server request too large')
        fd = self._process.stdin.fileno()
        while data:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not select.select([], [fd], [], remaining)[1]:
                raise ActorError('app-server write timeout')
            try:
                count = os.write(fd, data)
            except BlockingIOError:
                continue
            data = data[count:]

    def _receive(self, deadline):
        while b'\n' not in self._buffer:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not select.select([self._process.stdout], [], [], remaining)[0]:
                raise ActorError('app-server response timeout')
            data = os.read(self._process.stdout.fileno(), 65536)
            if not data:
                raise ActorError('app-server closed the protocol')
            self._event_bytes += len(data)
            if self._event_bytes > MAX_EVENT_BYTES:
                raise ActorError('app-server event limit exceeded')
            self._buffer.extend(data)
        line, _, remaining = self._buffer.partition(b'\n')
        self._buffer = bytearray(remaining)
        self._rpc_log.write(line + b'\n')
        self._rpc_log.flush()
        value = _json_loads(line.decode('utf-8'))
        if not isinstance(value, dict):
            raise ActorError('invalid app-server protocol message')
        return value

    def _notification(self, message, deadline):
        if 'id' in message:
            # Any server request (approval, tools, user input, authentication
            # recovery) invalidates this response-only actor. Never approve it.
            self._send({'id': message['id'], 'error': {
                'code': -32601, 'message': 'Requests are disabled for this actor'}}, deadline)
            raise ActorError('app-server requested a tool or unsupported capability')
        method, params = message.get('method'), message.get('params', {})
        if (method == 'warning' and self._turn is not None and not self._turn.started
                and params.get('threadId') == self.session_id
                and params.get('message') in STARTUP_NOTICES):
            return
        if (method == 'configWarning' and self._turn is None
                and params.get('summary') == BUNDLED_BWRAP_NOTICE
                and all(params.get(k) is None for k in ('details', 'path', 'range'))):
            return
        if method == 'remoteControl/status/changed':
            # Versioned RemoteControlStatusChangedNotification schema. This
            # adapter never enables remote control or exposes a remote server.
            if params.get('status') != 'disabled' or params.get('environmentId') is not None:
                raise ActorError('app-server remote control must remain disabled')
            return
        if method == 'thread/started':
            identity = _identifier(params['thread']['id'])
            if self.session_id not in (None, identity) or self._announced_thread not in (None, identity):
                raise ActorError('app-server started another thread')
            self._announced_thread = identity
        elif method in ('thread/status/changed', 'thread/name/updated'):
            expected = self.session_id or self._announced_thread
            if expected is None or params.get('threadId') != expected:
                raise ActorError('app-server metadata belongs to another thread')
        elif method in ('account/updated', 'account/rateLimits/updated'):
            pass
        elif self._turn is not None:
            self._turn.event(method, params)
        else:
            raise ActorError('unsupported app-server startup notification')

    def _rpc(self, method, params, deadline):
        identity = self._request_id
        self._request_id += 1
        self._send({'id': identity, 'method': method, 'params': params}, deadline)
        while True:
            message = self._receive(deadline)
            if 'method' in message:
                self._notification(message, deadline)
                continue
            if type(message.get('id')) is not int or message['id'] != identity:
                raise ActorError('app-server response ID mismatch')
            if 'error' in message or not isinstance(message.get('result'), dict):
                raise ActorError('app-server rejected the request; inspect private trace')
            return message['result']

    def invoke(self, prompt, images, schema):
        if not self._lock.acquire(blocking=False):
            raise ActorError('one actor may not execute concurrent decisions')
        started = time.perf_counter()
        try:
            if self._closed or self._failed:
                raise ActorError('actor is closed or has a failed turn')
            if not isinstance(prompt, str) or not prompt or len(prompt.encode()) > 256 * 1024:
                raise ValueError('prompt must be nonempty and at most 256 KiB')
            if not 1 <= len(images) <= 16:
                raise ValueError('one to sixteen designated public images required')
            validate_schema(None, schema, check_only=True)
            from PIL import Image
            directory = self.public / f'{self.calls:06d}'
            directory.mkdir(mode=0o700)
            _private_write(directory / 'prompt.txt', prompt)
            _private_write(directory / 'schema.json', json.dumps(schema, allow_nan=False))
            inputs = [{'type': 'text', 'text': prompt}]
            for index, path in enumerate(images):
                target = directory / f'camera-{index:02d}.png'
                with Image.open(path) as source:
                    if source.width * source.height > 4096 * 4096:
                        raise ValueError('public image exceeds size limit')
                    rgb = source.convert('RGB')
                    Image.frombytes('RGB', rgb.size, rgb.tobytes()).save(target, format='PNG')
                inputs.append({'type': 'localImage', 'path': '/public/' + directory.name + '/' + target.name})
            staged = time.perf_counter()
            deadline = time.monotonic() + self.timeout_s
            self._event_bytes = len(self._buffer)
            self._turn = TurnResult(self.session_id)
            result = self._rpc('turn/start', {
                'threadId': self.session_id, 'input': inputs, 'model': self.model,
                'effort': self.effort, 'approvalPolicy': 'never',
                'sandboxPolicy': {'type': 'readOnly'}, 'outputSchema': schema,
            }, deadline)
            self._turn.turn(result['turn'])
            while not self._turn.completed:
                self._notification(self._receive(deadline), deadline)
            received = time.perf_counter()
            decision = self._turn.result(schema)
            total = self._turn.usage_total
            if any(total[k] < self._usage_total.get(k, 0) for k in total):
                raise ActorError('app-server cumulative usage regressed')
            delta = {k: v - self._usage_total.get(k, 0) for k, v in total.items()}
            self._usage_total = total.copy()
            _private_write(self.events / f'decision-{self.calls:06d}.json',
                           json.dumps(decision, allow_nan=False))
            self.calls += 1
            return {'decision': decision, 'session_id': self.session_id,
                    'turn_id': self._turn.turn_id, 'wall_s': time.perf_counter() - started,
                    'usage': total, 'usage_scope': 'thread_total', 'turn_usage_delta': delta,
                    'last_reported_usage': self._turn.usage_last,
                    'model': self.model, 'effort': self.effort, 'cli_version': self.cli_version,
                    'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
                    'transport': 'experimental_app_server_stdio',
                    'staging_wall_s': staged - started,
                    'process_wall_s': received - staged,
                    'result_parse_wall_s': time.perf_counter() - received,
                    'server_startup_wall_s': self.startup_wall_s,
                    'provision_wall_s': self.provision_wall_s}
        except BaseException:
            self._failed = True
            try:
                self.close()
            except Exception:
                pass  # Preserve original error; close retains resource flags for retry.
            raise
        finally:
            self._turn = None
            self._lock.release()

    def close(self):
        try:
            super().close()
        finally:
            if self._process is not None:
                if self._process.poll() is None:
                    self._process.terminate()
                    try:
                        self._process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        self._process.kill()
                        self._process.wait(timeout=3)
                for stream in (self._process.stdin, self._process.stdout):
                    if stream and not stream.closed:
                        stream.close()
            for stream in (self._rpc_log, self._stderr_log):
                if stream and not stream.closed:
                    stream.close()
