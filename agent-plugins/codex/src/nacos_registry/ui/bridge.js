/* Copyright 2026 Alibaba Group Holding Ltd. SPDX-License-Identifier: Apache-2.0 */
'use strict';
globalThis.NacosBridge = class {
  constructor(onContext, entrypoint = 'unknown', onLaunch = () => {}) {
    this.sequence = 0; this.pending = new Map(); this.host = {}; this.entrypoint = entrypoint;
    window.addEventListener('message', event => {
      if (event.source !== parent || event.data?.jsonrpc !== '2.0') return;
      const message = event.data;
      if (message.method === 'ui/notifications/tool-result') {
        const value = message.params?.structuredContent;
        if (value?.status === 'ready' && value.launchId && (value.route === 'settings' || value.draft)) {
          this.launch = value; onLaunch(value);
        }
      }
      if (message.method === 'ui/notifications/host-context-changed') {
        this.host.hostContext = {...this.host.hostContext, ...message.params}; onContext(message.params);
      }
      if (message.method || (!Object.hasOwn(message, 'result') && !message.error)) return;
      const request = this.pending.get(message.id);
      if (!request) return;
      clearTimeout(request.timer); this.pending.delete(message.id);
      if (message.error) request.reject(Object.assign(new Error(message.error.message || '页面桥接失败'), {kind: 'bridge'}));
      else request.resolve(message.result);
    });
    this.onContext = onContext;
  }
  rpc(method, params = {}, timeout = 120000) {
    return new Promise((resolve, reject) => {
      const id = ++this.sequence;
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(Object.assign(new Error('等待响应超时。写操作可能已生效，请先核对待处理操作。'), {kind: 'timeout'}));
      }, timeout);
      this.pending.set(id, {resolve, reject, timer});
      parent.postMessage({jsonrpc: '2.0', id, method, params}, '*');
    });
  }
  async initialize() {
    this.host = await this.rpc('ui/initialize', {appInfo: {name: 'nacos-resource-center', version: NacosBuild.version},
      appCapabilities: {}, protocolVersion: '2026-01-26'}, 15000);
    this.onContext(this.host.hostContext || {});
    parent.postMessage({jsonrpc: '2.0', method: 'ui/notifications/initialized', params: {}}, '*');
    if (!this.host.hostCapabilities?.serverTools) throw new Error('当前应用不提供页面工具桥接，请通过对话使用插件。');
  }
  canMessageCurrentConversation() {
    if (!this.host.hostCapabilities?.message?.text) return false;
    if (this.entrypoint === 'global') return false;
    const context = this.host.hostContext || {}, tool = context.toolInfo?.tool;
    const entries = tool?._meta?.['openai/ui']?.entrypoints || [];
    // The tool selects an entrypoint-specific resource. Host toolInfo and conversation
    // IDs are optional; expansion changes layout, not the resource's entrypoint.
    if (tool?.name === 'nacos_open_center' || entries.some(x => x.type === 'global')) return false;
    if (this.entrypoint === 'thread') return true;
    if (tool?.name === 'nacos_open_center_panel' || entries.some(x => x.type === 'thread')) return true;
    return !!(context.conversationId || context.threadId);
  }
  async messageCurrentConversation(text) {
    if (!this.canMessageCurrentConversation()) throw Object.assign(new Error('请在目标对话中打开资源中心侧栏后使用。'), {kind: 'unsupported'});
    const result = await this.rpc('ui/message', {role: 'user', content: [{type: 'text', text}]});
    if (result?.isError) throw Object.assign(new Error('应用未接受这条使用说明。'), {kind: 'bridge'});
    return result;
  }
  async call(action, args = {}, context) {
    const response = await this.rpc('tools/call', {name: 'nacos_' + action,
      arguments: {...args, ...(context ? {_context: context} : {})}});
    return this.value(response);
  }
  value(response) {
    let value = response.structuredContent;
    if (value === undefined) {
      try { value = JSON.parse(response.content?.find(x => x.type === 'text')?.text || '{}'); }
      catch { throw Object.assign(new Error('工具返回无法解析；写操作请先核对记录。'), {kind: 'protocol'}); }
    }
    // Operation records are values, even when MCP sets isError. Keep evidence and recovery actions.
    if (response.isError && ['failed', 'result_unknown', 'recovery_required'].includes(value?.status)) return value;
    if (response.isError || value?.error) throw Object.assign(new Error(value.message || '操作未完成'), {kind: value.error, value});
    return value;
  }
  async saveCredentials(profile, changes, context) {
    // Only the encrypted JWE enters postMessage/MCP; this page never fetches localhost.
    const response = await this.rpc('tools/call', {name: 'nacos_credentials_begin', arguments: {_context: context}});
    this.value(response);
    const envelope = await NacosCredentialCrypto.seal(response._meta?.['nacos/credentialChannel'], {profile, changes});
    try {
      const result = await this.call('credentials_save', {envelope}, context);
      if (result?.status !== 'configured') throw new Error();
      return result;
    } catch (error) {
      throw Object.assign(new Error('无法确认凭据保存结果，请重新读取已保存设置核对。'), {kind: error.kind || 'credential_channel'});
    }
  }
};
