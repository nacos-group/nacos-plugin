# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
import copy
import base64
import hashlib
import json
from pathlib import Path
import struct
import unittest
from unittest.mock import patch

import test_core
from nacos_registry.errors import PluginError
from nacos_registry.hosts import native
from nacos_registry.server import DEFINITIONS, validate
from nacos_registry.service import Service
from nacos_registry.store import Store


class DiscoveryTests(unittest.TestCase):
    setUp = test_core.CoreTests.setUp
    tearDown = test_core.CoreTests.tearDown
    call = test_core.CoreTests.call

    def test_default_and_persistence_do_not_orphan_resources(self):
        plan = self.call('install_plan', name='sample-skill', installRoot=self.profile['installRoots'][0])
        self.call('apply', planId=plan['id'])
        before = self.call('status')
        self.assertEqual(before['discovery']['installPolicy'], 'ask')
        for mode in ('auto', 'never', 'ask'):
            self.call('configure_discovery', installPolicy=mode)
            reopened = Service(Store(self.root/'state'), lambda _: self.remote).invoke('status')
            self.assertEqual(reopened['discovery']['installPolicy'], mode)
            for key in ('context', 'profile', 'installations'):
                self.assertEqual(reopened[key], before[key])
        with self.assertRaises(PluginError): self.call('configure_discovery', installPolicy='sometimes')

    def test_implicit_plans_require_policy_and_explicit_install_is_independent(self):
        for kind in ('skill', 'mcp', 'agent'):
            for policy in ('ask', 'auto', 'never'):
                self.call('configure_discovery', installPolicy=policy)
                for mode in ('automatic', 'confirmed'):
                    kwargs = dict(discoveryReuse=mode)
                    if kind == 'skill':
                        action = 'install_plan'; kwargs.update(name='sample-skill', installRoot=self.profile['installRoots'][0])
                    else:
                        action = 'connection_plan'; kwargs.update(resourceType=kind, name='example-service')
                    with self.subTest(kind=kind, policy=policy, mode=mode):
                        # Rejection must happen before resolving or downloading a resource.
                        if policy == 'never' or (policy == 'ask' and mode == 'automatic'):
                            with self.assertRaises(PluginError) as error: self.call(action, **kwargs)
                            self.assertEqual(error.exception.kind, 'permission')
                        elif kind != 'agent':
                            self.assertEqual(self.call(action, **kwargs)['discoveryReuse'], mode)
        self.call('configure_discovery', installPolicy='never')
        plan = self.call('install_plan', name='sample-skill', installRoot=self.profile['installRoots'][0])
        self.assertEqual(self.call('apply', planId=plan['id'])['status'], 'completed')

    def test_policy_change_blocks_old_automatic_plan_before_writes(self):
        self.call('configure_discovery', installPolicy='auto')
        plan = self.call('install_plan', name='sample-skill', installRoot=self.profile['installRoots'][0], discoveryReuse='automatic')
        for policy in ('ask', 'never'):
            self.call('configure_discovery', installPolicy=policy)
            with self.assertRaises(PluginError): self.call('apply', planId=plan['id'])
            self.assertFalse(Path(plan['target']).exists())
        self.call('configure_discovery', installPolicy='auto')
        result = self.call('apply', planId=plan['id'])
        self.call('configure_discovery', installPolicy='never')
        self.assertEqual(self.call('apply', planId=plan['id']), result)

    def test_preview_requires_only_read_and_does_not_install_or_write_state(self):
        p = copy.deepcopy(self.profile); p['allowedOperations'] = ['read']; p['installRoots'] = []
        self.call('configure', profile=p)
        self.remote.content['guide.md'] = b'A bounded reference'
        before = self.service.store.file.read_bytes()
        result = self.call('preview_skill', name='sample-skill')
        self.assertFalse(result['installed'])
        self.assertIn('guide.md', result['files'])
        self.assertEqual(self.call('preview_skill', name='sample-skill', version=result['version'], file='guide.md')['content'], 'A bounded reference')
        self.assertEqual(before, self.service.store.file.read_bytes())
        self.assertFalse((self.root/'host').exists())
        for path in ('../state.json', '/absolute', 'missing.md'):
            with self.assertRaises(PluginError): self.call('preview_skill', name='sample-skill', file=path)
        self.remote.content['SKILL.md'] = test_core.files(name='wrong')['SKILL.md']
        with self.assertRaises(PluginError): self.call('preview_skill', name='sample-skill')

    def rpc(self, results):
        mock = patch('nacos_registry.remote.JsonRpc')
        rpc = mock.start(); self.addCleanup(mock.stop)
        rpc.return_value.initialize_mcp.return_value = {'capabilities': {'tools': {}}}
        rpc.return_value.request.side_effect = results
        return rpc.return_value

    def test_mcp_trial_calls_exact_tool_without_persistent_connection(self):
        self.call('configure_discovery', installPolicy='never')
        result_content = {'content': [{'type': 'text', 'text': 'private response'}], 'hostLoaded': 'true'}
        rpc = self.rpc([{'tools': [{'name': 'lookup'}]}, result_content])
        value = self.call('mcp_trial', name='sample-service', tool='lookup', arguments={'id': 'private input'})
        self.assertEqual(value['realUse'], 'completed')
        self.assertFalse(value['saved']); self.assertEqual(value['hostLoaded'], 'not_claimed')
        rpc.request.assert_called_with('tools/call', {'name': 'lookup', 'arguments': {'id': 'private input'}}, mutation=True)
        rpc.close_mcp.assert_called_once()
        self.assertEqual(self.call('status')['connections'], [])
        self.assertFalse(Path(self.profile['codexConfig']).exists())
        for secret in ('private input', 'private response'):
            self.assertNotIn(secret, self.service.store.file.read_text())

    def test_trial_list_and_unknown_tool_cannot_execute(self):
        rpc = self.rpc([{'tools': [{'name': 'lookup'}]}, {'tools': [{'name': 'lookup'}]}])
        before = self.service.store.file.read_bytes()
        self.assertEqual(self.call('mcp_trial', name='sample-service')['realUse'], 'not_performed')
        with self.assertRaises(PluginError): self.call('mcp_trial', name='sample-service', tool='delete_everything')
        self.assertTrue(all(call.args[0] == 'tools/list' for call in rpc.request.call_args_list))
        self.assertEqual(before, self.service.store.file.read_bytes())

    def test_trial_honors_existing_native_tool_restrictions(self):
        config = Path(self.profile['codexConfig']); config.parent.mkdir(parents=True)
        config.write_text('[mcp_servers.existing]\nurl="https://TOOLS.example.org/mcp/"\ndisabled_tools=["delete"]\n')
        rpc = self.rpc([{'tools': [{'name': 'lookup'}, {'name': 'delete'}]}])
        self.assertEqual([t['name'] for t in self.call('mcp_trial', name='sample-service')['tools']], ['lookup'])
        with self.assertRaises(PluginError): self.call('mcp_trial', name='sample-service', tool='delete')
        config.write_text(config.read_text()+'enabled=false\n')
        with self.assertRaises(PluginError): self.call('mcp_trial', name='sample-service')
        self.assertEqual(rpc.initialize_mcp.call_count, 1)

    def test_trial_unknown_outcome_and_tool_error_are_not_success(self):
        for error in (PluginError('result_unknown', 'Unverified'), {'content': [], 'isError': True}):
            rpc = self.rpc([{'tools': [{'name': 'lookup'}]}, error])
            result = self.call('mcp_trial', name='sample-service', tool='lookup')
            if isinstance(error, PluginError): self.assertEqual(result['status'], 'result_unknown')
            else: self.assertEqual(result['realUse'], 'failed')
            self.assertEqual(rpc.request.call_count, 2)

    def test_agent_trial_keeps_task_handle_without_reusable_binding(self):
        from test_ui_contract import UiContractTests
        UiContractTests.agent(self)
        with self.service.store.locked():
            self.service.data['connections'].clear(); self.service.store.save()
        with patch('nacos_registry.remote.JsonRpc') as rpc:
            rpc.return_value.request.return_value = {'kind': 'task', 'id': 'remote-task', 'status': {'state': 'working'}}
            result = self.call('agent_trial', name='sample-agent', text='private task')
            self.assertFalse(result['saved']); self.assertTrue(result['taskHandle'])
            rpc.return_value.request.return_value = {'kind': 'task', 'id': 'remote-task', 'status': {'state': 'completed'}}
            self.assertEqual(self.call('agent_task', taskHandle=result['taskHandle'])['result']['status']['state'], 'completed')
        self.assertEqual(self.call('status')['connections'], [])
        self.assertNotIn('private task', self.service.store.file.read_text())

    def test_trial_auth_and_tool_schema_boundaries(self):
        p=copy.deepcopy(self.profile);p['clientAuth']={'type':'token','tokenEnv':'REGISTRY_TOKEN'}
        self.call('configure', profile=p)
        with self.assertRaises(PluginError): self.call('mcp_trial', name='sample-service', auth={'type':'bearer','tokenEnv':'REGISTRY_TOKEN'})
        validate({'name':'example','tool':'lookup','arguments':{'nested':{'ids':[1,2]}}}, DEFINITIONS['mcp_trial'][1])
        for args in ({'name':'example','url':'https://arbitrary.example'}, {'name':'example','arguments':{'x':'a'*131073}}):
            with self.assertRaises(PluginError): validate(args, DEFINITIONS['mcp_trial'][1])


class NativeRefreshTests(unittest.TestCase):
    thread = '12345678-1234-1234-1234-123456789abc'

    def run_refresh(self, responses):
        with patch.object(native, 'control_socket', return_value='/fake/socket'), patch.object(native, 'ControlClient') as cls:
            client = cls.return_value; client.request.side_effect = responses
            result = native.refresh('nacos_test', self.thread, '/fake/config.toml')
            client.close.assert_called_once()
            return result, client

    def test_missing_control_socket_does_not_start_a_process(self):
        with patch.object(native, 'control_socket', side_effect=PluginError('native_unavailable', 'No socket')), patch.object(native, 'ControlClient') as cls:
            self.assertEqual(native.refresh('nacos_test', self.thread, '/fake/config.toml')['refresh'], 'unavailable')
            cls.assert_not_called()

    def test_different_app_server_does_not_refresh_or_resume(self):
        result, client = self.run_refresh([{}, {'data': ['other-thread']}])
        self.assertEqual(result['reason'], 'native_thread_mismatch')
        self.assertEqual([c.args[0] for c in client.request.call_args_list], ['initialize', 'thread/loaded/list'])

    def test_native_runtime_and_current_turn_are_distinct(self):
        result, client = self.run_refresh([{}, {'data':[self.thread]}, {}, {'data':[{'name':'nacos_test','runtimeStatus':'connected','tools':{'lookup':{}},'toolsError':None}]}])
        self.assertEqual(result['hostLoaded'], 'available')
        self.assertEqual(result['currentTurnTools'], 'unverified'); self.assertEqual(result['realUse'], 'unverified')
        self.assertEqual(client.request.call_args_list[-1].args[1]['threadId'], self.thread)
        self.assertNotIn('thread/start', [c.args[0] for c in client.request.call_args_list])

    def test_cached_catalog_does_not_claim_runtime_connected(self):
        result, _ = self.run_refresh([{}, {'data':[self.thread]}, {}, {'data':[{'name':'nacos_test','runtimeStatus':None,'tools':{'lookup':{}}}]}])
        self.assertEqual(result['refresh'], 'queued'); self.assertEqual(result['hostLoaded'], 'pending')

    def test_rejected_refresh_is_not_retried_or_claimed_loaded(self):
        result, client = self.run_refresh([{}, {'data':[self.thread]}, PluginError('native_rejected','Unsupported')])
        self.assertEqual(result['refresh'], 'unverified')
        self.assertEqual(result['hostLoaded'], 'unverified')
        self.assertEqual(len(client.request.call_args_list), 3)

    def test_websocket_handshake_fragment_ping_and_request_rejection(self):
        class Socket:
            def __init__(self): self.data = b''; self.sent = []; self.closed = False
            def settimeout(self, value): pass
            def connect(self, path): pass
            def close(self): self.closed = True
            def recv(self, size):
                value, self.data = self.data[:min(size, 3)], self.data[min(size, 3):]
                return value
            def sendall(self, data):
                self.sent.append(data)
                if data.startswith(b'GET '):
                    key = data.split(b'Sec-WebSocket-Key: ')[1].split(b'\r\n')[0]
                    accept = base64.b64encode(hashlib.sha1(key+b'258EAFA5-E914-47DA-95CA-C5AB0DC85B11').digest())
                    self.data = b'HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: '+accept+b'\r\n\r\n'
                    # Ping, unsolicited request, and fragmented text response.
                    request = b'{"id":99,"method":"item/approval"}'
                    self.data += b'\x89\x01x' + bytes([0x81,len(request)]) + request
                    response = b'{"id":1,"result":{"ok":true}}'
                    self.data += bytes([0x01,10])+response[:10]+bytes([0x80,len(response)-10])+response[10:]
        sock = Socket()
        with patch.object(native.socket, 'socket', return_value=sock):
            client=native.ControlClient('/fake/socket')
            self.assertEqual(client.request('initialize', {}), {'ok':True})
            client.close()
        self.assertTrue(sock.closed)
        messages=[]
        for frame in sock.sent[1:]:
            self.assertTrue(frame[1] & 128)
            size=frame[1]&127; offset=2
            if size==126: size=struct.unpack('!H',frame[2:4])[0];offset=4
            mask=frame[offset:offset+4]; payload=frame[offset+4:offset+4+size]
            decoded=bytes(c^mask[i%4] for i,c in enumerate(payload))
            if frame[0]&15 == 1: messages.append(json.loads(decoded))
        self.assertEqual(messages[-1], {'id':99,'error':{'code':-32601,'message':'Unsupported client request'}})

    def test_malformed_native_frames_are_rejected(self):
        for frame in (b'\x82\x00', b'\x81\x80', b'\x81\x7f'+struct.pack('!Q',native.MAX_FRAME+1)):
            client = native.ControlClient.__new__(native.ControlClient)
            from unittest.mock import Mock
            client.socket = Mock()
            data = bytearray(frame)
            def recv(count):
                value=bytes(data[:count]);del data[:count];return value
            client.socket.recv.side_effect=recv
            import time
            client.deadline=time.monotonic()+2
            with self.assertRaises(PluginError):client._message(time.monotonic()+2)
