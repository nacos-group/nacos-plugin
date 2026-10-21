/* Copyright 2026 Alibaba Group Holding Ltd. SPDX-License-Identifier: Apache-2.0 */
'use strict';
// Business navigation and operation rules have no DOM, theme or host dependency.
globalThis.NacosModel = (() => {
  const types = {skill: '技能', mcp: '工具服务', agent: '远端 Agent'};
  const labels = {
    pending_host_verification: '已安装，待应用加载确认', pending_host_reload: '配置已保存，待应用刷新',
    configured_unverified: '已接入，尚未检查连接', unavailable: '当前不可用', completed: '已完成',
    failed: '失败', result_unknown: '结果未知，请先核对', recovery_required: '需要恢复本地状态',
    running: '正在执行', draft: '草稿', online: '已发布', reviewing: '审核中', reviewed: '审核已完成',
    not_started: '尚未开始', awaiting_scan: '等待扫描', awaiting_selection: '等待选择', skipped: '已跳过',
    complete: '已完成', track: '仅跟踪', ignore: '已忽略', explicit: '已绑定远端', recovered: '已恢复',
    candidate: '可选择', unreadable: '无法读取',
    working: '处理中', submitted: '已接受', canceled: '已取消', rejected: '已拒绝',
    'input-required': '等待输入', 'auth-required': '需要认证', unknown: '尚未核验'
  };
  const label = s => labels[s] || s || '尚未核验';
  const action = name => ({
    upload: '保存草稿', install: '安装或更新技能', uninstall: '卸载技能', submit: '提交版本', publish: '发布版本',
    mcp_config: '保存工具连接', bind_agent: '保存 Agent 接入', disconnect: '解除接入',
    agent_send: '发送 Agent 任务', agent_task_get: '查询任务', agent_task_cancel: '请求取消任务', local_recovery: '恢复本地状态'
  }[name] || '资源操作');
  const identity = x => JSON.stringify([x.ref?.registryId, x.ref?.namespaceId, x.ref?.resourceType || x.resourceType || x.type,
    x.ref?.name || x.name || x.resourceName, x.version || x.resourceVersion, x.target || x.endpoint?.url]);
  const append = (old, items) => [...new Map([...old, ...items].map(x => [identity(x), x])).values()];
  // State is already scoped by the core. Require version and any supplied source, never name alone.
  const connectedMatches = (x, state) => [...(state.installations || []), ...(state.connections || [])].filter(item =>
    (x.ref?.resourceType || x.resourceType || x.type) === item.ref?.resourceType &&
    (x.ref?.name || x.name || x.resourceName) === item.ref?.name &&
    !!(x.version || x.resourceVersion) && (x.version || x.resourceVersion) === item.version &&
    (!x.ref?.registryId || x.ref.registryId === item.ref.registryId) &&
    (!x.ref?.namespaceId || x.ref.namespaceId === item.ref.namespaceId));
  const terminal = s => ['completed', 'failed', 'canceled', 'rejected'].includes(s);
  const canCancel = task => !!task?.taskHandle && !terminal(task.status) && !task.cancelRequested;
  const canPublish = version => {
    let review = version.publishPipelineInfo;
    try { if (typeof review === 'string') review = JSON.parse(review); } catch { return false; }
    return version.status === 'reviewed' && review?.status === 'APPROVED';
  };
  const menu = (type, view) => view === 'owned' ? [
    ['overview', '查看概览'], ['versions', '查看版本与发布'], ['local', '从本地更新草稿…']
  ] : ({
    skill: [['overview', '查看详情'], ['verify', '检查文件与访问'], ['update', '检查更新'], ['remove', '卸载技能…']],
    mcp: [['tools', '查看工具'], ['probe', '连接诊断'], ['connect', '更新连接设置…'], ['remove', '解除接入…']],
    agent: [['overview', '查看能力'], ['compose', '发起任务…'], ['task', '查看当前任务'], ['connect', '更新连接设置…'], ['remove', '解除接入…']]
  }[type] || []);
  const newSearch = () => ({query: '', type: '', items: [], cursor: null, submitted: false, error: null, loading: false, applied: null});
  class Workspace {
    constructor() {
      this.context = null; this.state = null; this.view = 'connected'; this.subpage = null;
      this.origin = null; this.origins = []; this.detail = null; this.stack = []; this.requests = new Map();
      this.search = newSearch();
      this.owned = {query: '', page: 1, items: [], total: 0, error: null};
      this.cache = {}; this.busy = new Set(); this.initial = true;
    }
    receive(state) {
      const changed = this.context !== null && this.context !== state.context;
      if (changed) {
        this.search = newSearch();
        this.owned = {query: '', page: 1, items: [], total: 0, error: null};
        this.detail = null; this.stack = []; this.cache = {}; this.requests.clear();
        this.origins = this.origins.map(o => ({...o, detail: null, stack: [], scroll: 0}));
        this.origin = this.origins.at(-1) || null;
      }
      this.context = state.context; this.state = state;
      if (this.initial) {
        this.view = (state.installations?.length || state.connections?.length) ? 'connected' : 'discover';
        this.initial = false;
      }
      return changed;
    }
    needsSearch() {
      return !!this.state?.profile && this.view === 'discover' && !this.subpage &&
        !this.search.submitted && !this.search.loading;
    }
    searchRequest(more = false) {
      const s = this.search;
      if (more && (s.loading || !s.cursor || !s.applied)) return null;
      const filters = more ? s.applied : {query: s.query.trim(), type: s.type};
      return {query: filters.query, limit: 20, ...(filters.type ? {resourceTypes: [filters.type]} : {}),
        ...(more ? {cursor: s.cursor} : {})};
    }
    begin(channel) {
      const request = {context: this.context, sequence: (this.requests.get(channel)?.sequence || 0) + 1};
      this.requests.set(channel, request); return request;
    }
    accepts(channel, request) { return request.context === this.context && this.requests.get(channel) === request; }
    open(detail) { if (this.detail) this.stack.push(this.detail); this.detail = detail; }
    back() { this.detail = this.stack.pop() || null; }
    returnTo(detail) {
      const index = this.stack.lastIndexOf(detail);
      if (index >= 0) this.stack.splice(index);
      this.detail = detail;
    }
    enter(page, scroll = 0) {
      if (this.subpage === page) return;
      this.origin = {view: this.view, subpage: this.subpage, detail: this.detail, stack: [...this.stack], scroll};
      this.origins.push(this.origin);
      this.subpage = page; this.detail = null; this.stack = [];
    }
    leave() {
      const o = this.origins.pop(); this.subpage = o?.subpage || null; this.origin = this.origins.at(-1) || null;
      if (o) { this.view = o.view; this.detail = o.detail; this.stack = o.stack; }
      return o?.scroll || 0;
    }
    async exclusive(key, task) {
      if (this.busy.size) throw Object.assign(new Error('已有写操作正在执行，请先等待结果。'), {kind: 'busy'});
      this.busy.add(key);
      try { return await task(); } finally { this.busy.delete(key); }
    }
  }
  return {Workspace, types, label, action, identity, append, connectedMatches, terminal, canCancel, canPublish, menu};
})();
