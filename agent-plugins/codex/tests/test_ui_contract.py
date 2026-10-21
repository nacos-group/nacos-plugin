# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
"""Core contracts needed by the workbench. All inputs are synthetic."""
import copy
import io
import json
import unittest
from unittest.mock import patch
import test_core
from nacos_registry.errors import PluginError
from nacos_registry.store import digest
from nacos_registry.ui import render_ui
from nacos_registry.server import serve, tools_list

class UiContractTests(unittest.TestCase):
    setUp = test_core.CoreTests.setUp
    tearDown = test_core.CoreTests.tearDown
    call = test_core.CoreTests.call

    def install(self):
        p = self.call('install_plan', name='sample-skill', installRoot=self.profile['installRoots'][0])
        return self.call('apply', planId=p['id'])['result']

    def agent(self):
        self.remote.discover = lambda *args: {
            "version": "1.0.0", "callInterfaces": [{"protocol": "a2a", "protocolVersion": "0.3.0",
                "nativeDescriptor": {"protocolVersion": "0.3.0", "preferredTransport": "JSONRPC"},
                "endpointSets": [{"source": "manual", "endpoints": [
                    {"uri": "https://agent.example.org/a2a", "transport": "JSONRPC"}]}]}]}
        with self.service.store.locked():
            item = dict(id='connection', ref=dict(resourceType='agent',name='sample-agent',registryId='example',namespaceId='test'),context=digest(self.service.data['profile']),version='1.0.0',endpoint=dict(url='https://agent.example.org/a2a'),auth=dict(type='none'))
            item['endpoint'].update(transport='JSONRPC', protocolVersion='0.3.0', source='manual')
            self.service.data['connections'][item['id']] = item
            self.service.store.save()

    def test_context_isolates_installs_tasks_and_operations(self):
        self.install(); self.agent()
        with patch('nacos_registry.remote.JsonRpc') as rpc:
            rpc.return_value.request.return_value = dict(kind='task',id='remote-task',status=dict(state='working'))
            sent = self.call('agent_send',connectionId='connection',text='private prompt not persisted')
        with self.service.store.locked():
            op = self.service.store.operation('upload',{'name':'sample-skill'})
            op['status']='result_unknown'; self.service.store.save()
        state=self.call('status')
        self.assertEqual(state['tasks'][0]['taskHandle'],sent['taskHandle'])
        self.assertNotIn('private prompt',json.dumps(state));self.assertNotIn('auth',state['tasks'][0])
        changed=copy.deepcopy(self.profile);changed['identityId']='other-user';self.call('configure',profile=changed)
        for key in ('installations','connections','tasks','unfinishedOperations'):self.assertEqual(self.call('status')[key],[],key)
        with self.assertRaises(PluginError):self.call('inspect_operation',operationId=op['id'])
        self.call('configure',profile=self.profile);self.assertEqual(len(self.call('status')['installations']),1)

    def test_plan_backed_legacy_operation_and_ambiguous_legacy_are_distinguished(self):
        plan=self.call('install_plan',name='sample-skill',installRoot=self.profile['installRoots'][0])
        with self.service.store.locked():
            self.service.data['operations']['legacy']=dict(id='legacy',action='install',status='running',planId=plan['id'])
            self.service.data['operations']['ambiguous']=dict(id='ambiguous',action='agent_send',status='running')
            self.service.store.save()
        self.assertEqual([x['id'] for x in self.call('status')['unfinishedOperations']],['legacy'])
        self.assertEqual(self.call('inspect_operation',operationId='legacy')['planId'],plan['id'])

    def test_local_conflict_has_exact_changes_and_keeps_files(self):
        self.install();target=self.root/'host/.agents/skills/sample-skill'
        (target/'SKILL.md').write_bytes(test_core.files(body='Local changes')['SKILL.md']);(target/'notes.txt').write_text('user notes')
        with self.assertRaises(PluginError) as caught:self.call('install_plan',name='sample-skill',installRoot=self.profile['installRoots'][0])
        c=caught.exception.details['conflict'];self.assertEqual(c['type'],'local_files')
        self.assertEqual(c['changes']['modified'],['SKILL.md']);self.assertEqual(c['changes']['added'],['notes.txt'])
        self.assertEqual((target/'notes.txt').read_text(),'user notes')

    def test_upload_binding_and_overwrite_are_independent(self):
        self.remote.meta=dict(name='sample-skill',editingVersion='1.0.0',versions=[dict(version='1.0.0',status='draft')])
        scan=self.call('scan');args=dict(scanId=scan['id'],candidateId=scan['items'][0]['id'])
        args['expectedContentHash']=self.call('upload_preview',**args)['contentHash']
        with self.assertRaises(PluginError) as caught:self.call('upload_plan',**args,overwriteDraft=True)
        self.assertTrue(caught.exception.details['conflict']['requiresBind']);self.assertEqual(self.remote.calls,[])
        with self.assertRaises(PluginError) as caught:self.call('upload_plan',**args,bindExisting=True)
        self.assertTrue(caught.exception.details['conflict']['requiresOverwrite'])
        self.assertFalse(any(x[0]=='upload' for x in self.remote.calls))
        self.assertEqual(self.call('upload_plan',**args,bindExisting=True,overwriteDraft=True)['action'],'OVERWRITE_DRAFT')

    def test_cancel_unknown_is_not_replayed_and_prompt_is_not_saved(self):
        self.agent()
        with patch('nacos_registry.remote.JsonRpc') as rpc:
            rpc.return_value.request.return_value=dict(kind='task',id='task-1',status=dict(state='working'))
            task=self.call('agent_send',connectionId='connection',text='ephemeral content')['taskHandle']
            rpc.return_value.request.side_effect=PluginError('result_unknown','Cancellation timed out')
            self.assertEqual(self.call('agent_task',taskHandle=task,action='cancel')['status'],'result_unknown')
            calls=rpc.return_value.request.call_count
            with self.assertRaises(PluginError):self.call('agent_task',taskHandle=task,action='cancel')
            self.assertEqual(rpc.return_value.request.call_count,calls)
            rpc.return_value.request.side_effect=None;rpc.return_value.request.return_value=dict(kind='task',id='task-1',status=dict(state='canceled'))
            self.call('agent_task',taskHandle=task)
        self.assertEqual(self.call('status')['tasks'][0]['status'],'canceled')
        self.assertEqual(self.call('status')['unfinishedOperations'],[])
        self.assertNotIn('ephemeral content',(self.root/'state/state.json').read_text())

    def test_known_cancel_failure_can_be_retried_explicitly(self):
        self.agent()
        with patch('nacos_registry.remote.JsonRpc') as rpc:
            rpc.return_value.request.return_value=dict(kind='task',id='task-2',status=dict(state='working'))
            task=self.call('agent_send',connectionId='connection',text='hello')['taskHandle']
            rpc.return_value.request.side_effect=PluginError('permission','Denied');self.call('agent_task',taskHandle=task,action='cancel')
        self.assertFalse(self.call('status')['tasks'][0]['cancelRequested'])

    def test_task_without_reference_remains_unknown(self):
        self.agent()
        with patch('nacos_registry.remote.JsonRpc') as rpc:
            rpc.return_value.request.return_value=dict(kind='task',status=dict(state='working'))
            value=self.call('agent_send',connectionId='connection',text='hello')
        self.assertEqual(value['status'],'result_unknown');self.assertEqual(self.call('status')['tasks'],[])

    def test_ui_is_self_contained_and_uses_safe_text_rendering(self):
        html=render_ui()
        for value in ('/* APP_STYLE */','/* APP_SCRIPT */','<script src=','<link ','innerHTML'):self.assertNotIn(value,html)
        for value in ('NacosModel','NacosBridge','NacosUI','已接入','发现资源','我的资源'):self.assertIn(value,html)

    def test_each_ui_tool_reads_its_own_entrypoint_resource(self):
        entries = [t for t in tools_list() if 'resourceUri' in t['_meta']['ui']]
        self.assertEqual(len({t['_meta']['ui']['resourceUri'] for t in entries}), 2)
        requests = [{'id': 1, 'method': 'initialize', 'params': {}}]
        for i, tool in enumerate(entries, 2):
            requests.append({'id': i, 'method': 'resources/read',
                             'params': {'uri': tool['_meta']['ui']['resourceUri']}})
        out = io.StringIO()
        serve(self.service, io.StringIO('\n'.join(json.dumps({'jsonrpc':'2.0', **x}) for x in requests)), out)
        pages = [json.loads(x)['result']['contents'][0] for x in out.getvalue().splitlines()[1:]]
        for tool, page in zip(entries, pages):
            self.assertEqual(page['uri'], tool['_meta']['ui']['resourceUri'])
            kind = tool['_meta']['openai/ui']['entrypoints'][0]['type']
            self.assertIn('"entrypoint": "' + kind + '"', page['text'])
            self.assertIn('NacosBuild.entrypoint', page['text'])
        self.assertEqual(self.remote.calls, [])

    def test_unavailable_page_returns_error_without_closing_connection(self):
        tool = next(t for t in tools_list() if t['name'] == 'nacos_open_center_panel')
        requests = [
            {'id': 1, 'method': 'initialize', 'params': {}},
            {'id': 2, 'method': 'resources/read', 'params': {'uri': tool['_meta']['ui']['resourceUri']}},
            {'id': 3, 'method': 'tools/call', 'params': {'name': tool['name'], 'arguments': {}}},
            {'id': 4, 'method': 'ping'},
        ]
        out = io.StringIO()
        with patch('nacos_registry.server.render_ui', side_effect=FileNotFoundError('private bundle path')):
            serve(self.service, io.StringIO('\n'.join(json.dumps({'jsonrpc':'2.0', **x}) for x in requests)), out)
        replies = [json.loads(x) for x in out.getvalue().splitlines()]
        self.assertEqual(replies[1]['error']['code'], -32603)
        self.assertIn('Restart Codex', replies[1]['error']['message'])
        self.assertTrue(replies[2]['result']['isError'])
        self.assertIn('ui_unavailable', replies[2]['result']['content'][0]['text'])
        self.assertEqual(replies[3]['result'], {})
        self.assertNotIn('private bundle path', out.getvalue())

    def test_old_page_uri_does_not_change_entrypoint_or_close_connection(self):
        requests = [
            {'id': 1, 'method': 'initialize', 'params': {}},
            {'id': 2, 'method': 'resources/read', 'params': {'uri': 'ui://nacos-ai-registry/old-page.html'}},
            {'id': 3, 'method': 'ping'},
        ]
        out = io.StringIO()
        serve(self.service, io.StringIO('\n'.join(json.dumps({'jsonrpc':'2.0', **x}) for x in requests)), out)
        replies = [json.loads(x) for x in out.getvalue().splitlines()]
        self.assertEqual(replies[1]['error']['code'], -32002)
        self.assertIn('invoke', replies[1]['error']['message'])
        self.assertEqual(replies[2]['result'], {})
