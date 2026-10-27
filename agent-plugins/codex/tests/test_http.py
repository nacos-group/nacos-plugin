# Copyright 2026 Alibaba Group Holding Ltd.
# SPDX-License-Identifier: Apache-2.0
import json
import os
import unittest
from http.client import IncompleteRead
from unittest.mock import patch
from urllib.parse import parse_qs,urlsplit

from nacos_registry.registry import Registry
from nacos_registry.downstream import endpoints, JsonRpc
from nacos_registry.errors import PluginError
from nacos_registry.transport import http


class HttpContractTests(unittest.TestCase):
    def setUp(self):
        self.registry = Registry({"namespaceId": "example", "clientUrl": "https://registry.example.org/context", "adminUrl": "https://admin.example.org/context", "clientAuth": {"type": "token", "tokenEnv": "TEST_CLIENT_TOKEN"}, "adminAuth": {"type": "token", "tokenEnv": "TEST_ADMIN_TOKEN"}})
        self.env = patch.dict(os.environ, {"TEST_CLIENT_TOKEN": "client-test-value", "TEST_ADMIN_TOKEN": "admin-test-value", "TEST_DOWNSTREAM_TOKEN": "downstream-test-value"})
        self.env.start()
    def tearDown(self): self.env.stop()

    def test_client_context_path_cursor_and_auth(self):
        with patch('nacos_registry.registry.http', return_value=(200,{},b'{"code":0,"data":{"items":[],"nextCursor":"opaque"}}')) as http:
            result=self.registry.search(query="a b",cursor="a+/=",resourceTypes=["mcp","skill"])
            args=http.call_args.args; query=parse_qs(urlsplit(args[0]).query)
            self.assertEqual(urlsplit(args[0]).path,"/context/v3/client/ai/resources/search")
            self.assertEqual(query['cursor'],['a+/='])
            self.assertEqual(query['resourceTypes'],['mcp','skill'])
            self.assertEqual(args[2],{'accessToken':'client-test-value'})
            self.assertEqual(result['nextCursor'],'opaque')

    def test_capability_search_defaults_to_all_types_and_preserves_filters(self):
        payload = {"items": [{"name": "query-analyzer", "resourceType": "mcp"}], "nextCursor": "opaque+/="}
        with patch('nacos_registry.registry.http', return_value=(200, {}, json.dumps({"code": 0, "data": payload}).encode())) as send:
            first = self.registry.search(query="slow query", tagsAll=["database"])
            self.registry.search(query="slow query", tagsAll=["database"], cursor=first["nextCursor"])
        self.assertEqual(send.call_count, 2)
        queries = []
        for call in send.call_args_list:
            url, method, headers, *_ = call.args
            query = parse_qs(urlsplit(url).query)
            self.assertEqual(urlsplit(url).netloc, "registry.example.org")
            self.assertEqual(method, "GET")
            self.assertEqual(headers, {"accessToken": "client-test-value"})
            self.assertEqual(query["query"], ["slow query"])
            self.assertEqual(query["namespaceId"], ["example"])
            self.assertEqual(query["resourceTypes"], ["skill", "mcp", "agent"])
            self.assertEqual(query["limit"], ["20"])
            self.assertEqual(query["tagsAll"], ["database"])
            queries.append(query)
        self.assertEqual(queries[1].pop("cursor"), ["opaque+/="])
        self.assertEqual(queries[0], queries[1])
        self.assertEqual(first, payload)

    def test_upload_never_autopublishes(self):
        with patch('nacos_registry.registry.http', return_value=(200,{},b'{"code":0,"data":"sample"}')) as http:
            self.registry.upload(b'zip-data','CREATE_DRAFT','1.0.0','test')
            args=http.call_args.args
            self.assertIn('admin.example.org/context/v3/admin/ai/skills/upload',args[0])
            self.assertEqual(args[2]['accessToken'],'admin-test-value')
            self.assertIn(b'name="autoPublishIfNew"\r\n\r\nfalse',args[3])
            self.assertIn(b'name="uploadAction"\r\n\r\nCREATE_DRAFT',args[3])

    def test_owned_skills_uses_authenticated_principal_and_preserves_pagination(self):
        registry = Registry({**self.registry.profile, "identityId": "untrusted-local-label", "adminAuth": {
            "type": "login", "usernameEnv": "TEST_CLIENT_TOKEN", "passwordEnv": "TEST_ADMIN_TOKEN"}})
        def respond(url, method, headers, data, **kwargs):
            if url.endswith('/login'):
                return 200, {}, b'{"accessToken":"native-test-token","tokenTtl":60}'
            query = parse_qs(urlsplit(url).query)
            self.assertEqual(query['owner'], ['client-test-value'])
            self.assertEqual(query['pageNo'], ['2'])
            self.assertEqual(query['pageSize'], ['1'])
            return 200, {}, b'{"code":0,"data":{"pageItems":[{"name":"owned","owner":"client-test-value"}],"totalCount":3}}'
        with patch('nacos_registry.registry.http', side_effect=respond):
            result = registry.my_skills(page=2, limit=1)
        self.assertTrue(result['hasMore'])
        self.assertEqual(result['owner'], 'client-test-value')

    def test_owned_skills_rejects_unknown_identity_and_foreign_owner(self):
        with patch('nacos_registry.registry.http') as send:
            with self.assertRaises(PluginError): self.registry.my_skills()
            send.assert_not_called()
        registry = Registry({**self.registry.profile, "adminAuth": {
            "type": "login", "usernameEnv": "TEST_CLIENT_TOKEN", "passwordEnv": "TEST_ADMIN_TOKEN"}})
        with patch.object(registry, 'headers', return_value={}), patch.object(registry, 'request', return_value={
                'pageItems': [{'name': 'shared', 'owner': 'another-user'}], 'totalCount': 1}):
            with self.assertRaises(PluginError) as caught: registry.my_skills()
            self.assertEqual(caught.exception.kind, 'protocol')

    def test_login_403_is_authentication_not_resource_permission(self):
        registry = Registry({**self.registry.profile, "clientAuth": {"type": "login", "usernameEnv": "TEST_CLIENT_TOKEN", "passwordEnv": "TEST_ADMIN_TOKEN"}})
        with patch('nacos_registry.registry.http', side_effect=PluginError('permission', 'login rejected', httpStatus=403)) as send:
            with self.assertRaises(PluginError) as caught:
                registry.search()
            self.assertEqual(caught.exception.kind, 'authentication')
            self.assertEqual(registry.tokens, {})
            send.assert_called_once()

    def test_malformed_write_response_is_unknown(self):
        with patch('nacos_registry.registry.http', return_value=(200,{},b'not-json')):
            with self.assertRaises(PluginError) as caught: self.registry.lifecycle('sample','1.0.0','submit')
            self.assertEqual(caught.exception.kind,'result_unknown')

    def test_exact_version_header_required(self):
        with patch('nacos_registry.registry.http', return_value=(200,{'content-type':'application/zip'},b'PKdata')):
            with self.assertRaises(PluginError) as caught:self.registry.download('sample')
            self.assertEqual(caught.exception.kind,'unsupported')

    def test_native_mcp_backend_is_distinct_from_plain_http_backend(self):
        detail = {"protocol": "mcp-streamable", "backendEndpoints": [{"protocol": "https", "address": "tools.example.org", "port": 443, "path": "/mcp"}]}
        self.assertEqual(endpoints("mcp", detail)[0]["url"], "https://tools.example.org:443/mcp")
        detail["protocol"] = "http"
        detail["frontProtocol"] = "mcp-streamable"
        with self.assertRaises(PluginError): endpoints("mcp", detail)
        detail["protocol"] = "mcp-streamable"
        detail["backendEndpoints"][0]["protocol"] = None
        with self.assertRaises(PluginError): endpoints("mcp", detail)

    def test_agent_descriptor_and_source_precedence(self):
        detail={'callInterfaces':[{'protocol':'a2a','protocolVersion':'0.3.0','nativeDescriptor':{'protocolVersion':'0.3.0','preferredTransport':'JSONRPC'},'endpointSourceOrder':['RUNTIME','DECLARED'],'endpointSets':[{'source':'DECLARED','endpoints':[{'uri':'https://static.example.org','transport':'JSONRPC'}]},{'source':'RUNTIME','endpoints':[{'uri':'https://runtime.example.org','transport':'JSONRPC','healthy':True}]}]}]}
        self.assertEqual(endpoints('agent',detail)[0]['url'],'https://runtime.example.org')
        detail['callInterfaces'][0]['protocolVersion']='0.2.0'
        with self.assertRaises(PluginError):endpoints('agent',detail)

    def test_downstream_auth_is_independent_and_ids_checked(self):
        def http(url,method,headers,data,**kwargs):
            self.assertEqual(headers['Authorization'],'Bearer downstream-test-value')
            self.assertNotIn('accessToken',headers)
            request=json.loads(data)
            return 200,{},json.dumps({'jsonrpc':'2.0','id':request['id'],'result':{'kind':'message','parts':[]}}).encode()
        with patch('nacos_registry.downstream.http',side_effect=http):
            rpc=JsonRpc('https://agent.example.org/rpc',{'type':'bearer','tokenEnv':'TEST_DOWNSTREAM_TOKEN'})
            self.assertEqual(rpc.request('message/send',{},mutation=True)['kind'],'message')
        with patch('nacos_registry.downstream.http',return_value=(200,{},b'{"jsonrpc":"2.0","id":"wrong","result":{}}')):
            with self.assertRaises(PluginError) as caught:rpc.request('message/send',{},mutation=True)
            self.assertEqual(caught.exception.kind,'result_unknown')

    def test_truncated_http_response_never_makes_a_write_retryable(self):
        for mutation, expected in ((False, 'connection'), (True, 'result_unknown')):
            with self.subTest(mutation=mutation), patch('nacos_registry.transport.request.build_opener') as opener:
                response = opener.return_value.open.return_value.__enter__.return_value
                response.read.side_effect = IncompleteRead(b'partial', 10)
                with self.assertRaises(PluginError) as caught:
                    http('https://tools.example.org/rpc', 'POST', data=b'{}', mutation=mutation)
                self.assertEqual(caught.exception.kind, expected)
                opener.return_value.open.assert_called_once()

    def test_malformed_event_response_preserves_unknown_write_outcome(self):
        for body in (b'data: invalid\n\n', b'data: \xff\n\n'):
            for mutation, expected in ((False, 'protocol'), (True, 'result_unknown')):
                with self.subTest(body=body, mutation=mutation), patch('nacos_registry.downstream.http', return_value=(200, {'content-type': 'text/event-stream'}, body)) as send:
                    with self.assertRaises(PluginError) as caught:
                        JsonRpc('https://tools.example.org/rpc', {'type': 'none'}).request('tasks/cancel', {}, mutation=mutation)
                    self.assertEqual(caught.exception.kind, expected)
                    send.assert_called_once()


if __name__=='__main__': unittest.main()
