/* Copyright 2026 Alibaba Group Holding Ltd. SPDX-License-Identifier: Apache-2.0 */
'use strict';
(() => {
  const M = NacosModel, U = NacosUI, {h, button, badge, raw, empty, field, select, check, notify} = U;
  const model = new M.Workspace(), $ = s => document.querySelector(s);
  let localSelection = new Set(), localResults = null, upload = null;
  let typeFilter = '', lastTrigger = null, navigationId = 0, handoffPending = false;
  const workspaces = {}, toolCache = new Map();
  const add = (node, ...children) => node.append(...children.flat(Infinity).filter(x => x !== null && x !== undefined && x !== false));
  const bridge = new NacosBridge(context => {
    const root = document.documentElement;
    root.dataset.theme = context.theme || root.dataset.theme || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    for (const [key, value] of Object.entries(context.styles?.variables || {}))
      if (/^--[a-zA-Z0-9-]+$/.test(key) && typeof value === 'string') root.style.setProperty(key, value);
    const roles = {'--color-background-primary':'--page', '--color-background-secondary':'--surface', '--color-text-primary':'--text', '--color-text-secondary':'--muted', '--color-border-primary':'--line', '--color-background-inverse':'--primary', '--color-text-inverse':'--on-primary', '--color-text-danger':'--danger', '--color-text-warning':'--warning', '--color-text-success':'--good'};
    for (const [native, role] of Object.entries(roles)) if (typeof context.styles?.variables?.[native] === 'string') root.style.setProperty(role, `var(${native})`);
    if (context.locale && model.state && model.subpage === 'settings') queueMicrotask(render);
    updateHandoffButtons();
    const insets = context.safeAreaInsets;
    if (insets) for (const side of ['top', 'right', 'bottom', 'left']) root.style.setProperty('--safe-' + side, Math.max(0, Number(insets[side]) || 0) + 'px');
  }, NacosBuild.entrypoint);
  const preferences = NacosSettings.create({state: () => model.state,
    locale: () => bridge.host.hostContext?.locale || navigator.language, version: NacosBuild.version,
    busy: () => model.busy.size > 0, changed: () => { if (model.subpage === 'settings') render(); },
    diagnose: () => call('diagnose'), configure: profile => mutation('configure', {profile})});
  const canHandoff = () => bridge.canMessageCurrentConversation();
  const handoffLabel = () => canHandoff() ? '在当前对话中使用' : '复制使用说明';
  function updateHandoffButtons() {
    for (const node of document.querySelectorAll('[data-handoff]')) {
      node.textContent = handoffLabel(); node.disabled = handoffPending;
    }
    for (const node of document.querySelectorAll('[data-handoff-hint]')) node.hidden = canHandoff();
  }
  function handoffButton(x, kind = '') {
    const node = button(handoffLabel(), () => handoff(x), {kind, disabled: handoffPending});
    node.dataset.handoff = 'true'; return node;
  }
  const scope = name => model.state?.profile?.allowedOperations?.includes(name);
  const visibility = value => ({PRIVATE: '私有', PUBLIC: '公开', server_default_unknown: '采用服务端默认，尚未核实'}[value] || value);
  const nameOf = x => x.ref?.name || x.name || x.resourceName || '未命名资源';
  const typeOf = x => x.ref?.resourceType || x.resourceType || x.type || 'skill';
  const versionOf = x => x.version || x.resourceVersion;
  const connectionOf = x => x.id ? model.state.connections.find(c => c.id === x.id) : M.connectedMatches(x, model.state).find(c => c.endpoint);
  const currentTasks = x => (model.state?.tasks || []).filter(t => t.connectionId === x.id);
  const kv = pairs => h('dl', {class: 'key-value'}, pairs.filter(x => x[1] !== undefined && x[1] !== null && x[1] !== '').map(([key, value]) => [h('dt', {}, key), h('dd', {}, value)]));
  const backButton = () => button(model.stack.length ? '‹ 返回上一步' : '‹ 返回资源列表', () => { model.back(); renderDetail(); if (!model.detail) restoreFocus(); }, {kind: 'quiet detail-back'});
  function restoreFocus() { if (lastTrigger?.isConnected) lastTrigger.focus(); else $('#main h2')?.focus(); }
  async function call(action, args = {}) { return bridge.call(action, args, model.context); }
  async function load() {
    const state = await bridge.call('status');
    if (model.receive(state)) {
      navigationId++; toolCache.clear(); localSelection.clear(); upload = null; localResults = null; selectedOperation = null;
      preferences.reset();
      for (const key of Object.keys(workspaces)) delete workspaces[key];
      notify('连接上下文已变化，旧选择和计划已失效。');
    }
    return state;
  }
  async function refresh() {
    await load();
    if (!model.subpage && model.view === 'owned' && scope('develop')) return ownedPage(model.owned.page);
    if (!model.subpage && model.view === 'discover') return searchPage(false);
    render();
  }
  function locks() {
    for (const node of document.querySelectorAll('[data-write]')) node.disabled = !!model.busy.size || node.dataset.blocked === 'true';
    for (const node of document.querySelectorAll('.busy-label')) node.textContent = model.busy.size ? '操作进行中 · 可以继续浏览' : '';
  }
  async function mutation(action, args) {
    return model.exclusive(action, async () => {
      locks();
      try { const result = await call(action, args); await load(); return result; }
      finally { queueMicrotask(locks); }
    }).finally(locks);
  }
  function actionButton(text, fn, required, kind = '') {
    const blocked = required && !scope(required), reason = blocked ? '当前操作范围未启用；服务端权限仍需核验。' : undefined;
    const node = button(text, async event => {
      node.disabled = true; node.textContent = '正在处理…';
      try { return await fn(event); }
      finally { if (node.isConnected) { node.textContent = text; locks(); } }
    }, {disabled: blocked || model.busy.size > 0, reason, kind});
    node.dataset.write = 'true'; node.dataset.blocked = String(!!blocked); return node;
  }
  function form(fields, text, fn, draft = {}, required, options = {}) {
    const errorBox = h('p', {class: 'error', role: 'status'}, required && !scope(required) ? '尚未启用所需操作范围，请在设置中核对。' : '');
    const blocked = !!required && !scope(required);
    const submit = h('button', {type: 'submit', class: 'primary', disabled: blocked || !!model.busy.size,
      'data-write': 'true', 'data-blocked': String(blocked)}, text);
    const f = h('form', {class: options.className || 'step'}, fields, errorBox, h('div', {class: options.className?.includes('search-form') ? 'actions' : 'actions action-bar'}, options.back || null, submit));
    for (const input of f.querySelectorAll('input,textarea,select')) {
      if (Object.hasOwn(draft, input.name)) { if (input.type === 'checkbox') input.checked = draft[input.name] === true; else input.value = draft[input.name]; }
    }
    const capture = () => { for (const input of f.querySelectorAll('input,textarea,select')) draft[input.name] = input.type === 'checkbox' ? input.checked : input.value; };
    f.addEventListener('input', capture); f.addEventListener('change', capture);
    f.addEventListener('submit', async event => {
      event.preventDefault(); if (submit.disabled) return; capture(); submit.disabled = true; submit.textContent = '正在处理…'; errorBox.textContent = '';
      try { await fn(new FormData(f), draft); }
      catch (error) { errorBox.textContent = readable(error); if (error.kind === 'conflict') add(errorBox, raw(error.value)); }
      finally { if (submit.isConnected) { submit.disabled = required && !scope(required) || !!model.busy.size; submit.textContent = text; } }
    });
    return f;
  }
  function readable(error) {
    return ({permission: '没有操作权限，请核对身份和本地操作范围。', authentication: '认证失败，请检查所引用的环境变量。',
      not_found: '当前上下文中未找到该资源。', conflict: '输入、文件或远端状态发生变化，请核对后重新规划。',
      network: '无法连接服务，已有输入保持不变。', review_rejected: '审核未通过，不能发布。', review_unverified: '无法核实审核通过，不能发布。',
      unsupported: '当前适配尚不支持这项能力。', configuration: '需要先完成连接、目录或服务配置。'})[error.kind] || error.message;
  }
  function setDetail(value, push = true) {
    model.begin('detail');
    if (model.detail?.resource && value?.resource && M.identity(model.detail.resource) !== M.identity(value.resource)) { model.detail = null; model.stack = []; }
    if (push) model.open(value); else { model.detail = value; model.stack = []; }
    renderDetail(); $('#detail h2')?.focus();
  }
  function captureView() { workspaces[model.view] = {detail: model.detail, stack: [...model.stack], scroll: scrollY}; }
  function navigate(view) {
    U.closeOverlay(false); captureView(); model.subpage = null; model.origin = null; model.origins = []; model.view = view; navigationId++;
    const prior = workspaces[view]; model.detail = prior?.detail || null; model.stack = prior?.stack || [];
    render(); scrollTo(0, prior?.scroll || 0);
    if (view === 'owned' && scope('develop') && !model.owned.loaded) ownedPage(1);
  }
  function enterSettings() {
    if (model.busy.size) return notify('请等待当前写操作结束后修改配置。', true);
    model.enter('settings', scrollY); navigationId++; render();
  }
  function leaveSubpage() {
    const position = model.leave(); navigationId++; render(); scrollTo(0, position); restoreFocus();
  }
  function enterLocal() {
    model.enter('local', scrollY); navigationId++; render();
  }
  function header() {
    const p = model.state?.profile, setting = model.subpage === 'settings';
    $('#header').replaceChildren();
    $('#workspace').classList.toggle('in-settings', setting);
    if (setting) {
      add($('#header'), button('‹ ' + preferences.t('back'), leaveSubpage, {kind: 'quiet settings-back'}),
        h('div', {class: 'settings-heading'}, h('h1', {}, preferences.t('settings')),
          h('div', {class: 'context'}, p ? `${p.displayName || p.id} · ${p.namespaceId}` : preferences.t('unconfigured'))));
    } else {
      add($('#header'), h('div', {class: 'title-block workspace-heading'}, h('h1', {}, '资源中心'),
        h('div', {class: 'context'}, p ? `${p.displayName || p.id} · ${p.namespaceId}` : '尚未配置资源中心')),
        h('div', {class: 'toolbar'}, button('待处理操作' + ((model.state?.unfinishedOperations?.length || 0) ? ` (${model.state.unfinishedOperations.length})` : ''), () => { selectedOperation = null; model.enter('operations', scrollY); render(); }, {kind: 'quiet'}),
          button('设置', enterSettings, {kind: 'quiet'}), button('刷新', refresh, {kind: 'quiet'})));
    }
    const nav = $('#navigation'); nav.hidden = setting || !p;
    nav.replaceChildren(...[['connected', '已接入'], ['discover', '发现资源'], ['owned', '我的资源']].map(([id, label]) => {
      const b = button(label, () => navigate(id)); b.setAttribute('aria-current', model.view === id ? 'page' : 'false'); return b;
    }));
  }
  function render() {
    header(); $('#main').lang = 'zh-CN'; $('#main').replaceChildren(); $('#detail').replaceChildren(); $('#layout').classList.remove('has-detail');
    if (!model.state?.profile && model.subpage !== 'settings') {
      add($('#main'), h('h2', {tabindex: '-1'}, '连接 Nacos'), h('p', {class: 'muted'}, '先连接资源中心，再发现和接入需要的能力。本地技能盘点可稍后进行。'), button('连接 Nacos', enterSettings, {kind: 'primary'})); return;
    }
    $('#main').dataset.page = model.subpage || model.view;
    if (model.subpage) ({settings, local: localSkills, upload: uploadPage, operations: operations})[model.subpage]();
    else ({connected, discover, owned})[model.view]();
    if (!model.subpage) renderDetail(); locks();
    if (model.needsSearch()) queueMicrotask(() => { if (model.needsSearch()) searchPage(false); });
  }
  function resourceRow(x, view = model.view) {
    const type = typeOf(x), selected = model.detail?.resource && M.identity(model.detail.resource) === M.identity(x);
    const matches = view === 'discover' ? M.connectedMatches(x, model.state) : [];
    const primary = view === 'owned' ? '版本与发布' : type === 'mcp' ? '查看工具' : type === 'agent' ? '发起任务' : '查看详情';
    const open = event => { lastTrigger = event.currentTarget; openResource(x, view); };
    const actions = h('div', {class: 'resource-actions'}, button(view === 'discover' ? matches.length ? '查看接入' : type === 'skill' ? '安装技能' : type === 'mcp' ? '查看服务' : '查看能力' : primary, event => {
      lastTrigger = event.currentTarget;
      if (matches.length) return matches.length === 1 ? openResource(matches[0], view) : navigate('connected');
      if (view === 'discover') return type === 'skill' ? install(x) : openResource(x, view);
      if (view === 'owned') return versions(x);
      if (type === 'agent') return compose(x);
      if (type === 'mcp') return tools(x);
      return openResource(x, view);
    }, {kind: 'quiet'}));
    if (view !== 'discover') add(actions, button('⋯', event => more(event.currentTarget, x, view), {kind: 'quiet more', label: nameOf(x) + ' 更多操作'}));
    const state = x.loadState || x.status || (matches.length ? '已接入' : view === 'discover' ? '未接入' : '');
    const published = x.labels?.latest || x.versions?.filter(v => v.status === 'online').map(v => v.version).join(' / ');
    return h('article', {class: 'resource-row' + (selected ? ' selected' : ''), 'data-resource': M.identity(x),
      'data-connections': matches.map(item => item.id).join(',')}, h('span', {class: 'resource-icon', 'aria-hidden': 'true'}, {skill: 'S', mcp: 'M', agent: 'A'}[type]),
      h('div', {class: 'resource-info'}, button(nameOf(x), open, {kind: 'quiet resource-name'}), h('div', {class: 'description'}, x.description || x.summary || ''),
        view !== 'owned' ? h('div', {class: 'metadata'}, `${M.types[type] || type} · ${versionOf(x) || (type === 'skill' ? '接入前解析版本' : type === 'mcp' ? 'Streamable HTTP' : 'A2A')}`,
          x.target ? h('span', {class: 'resource-path', title: x.target}, x.target) : null) : null,
        view === 'owned' ? h('div', {class: 'row-badges'}, badge('已发布 ' + (published || '暂无')), x.editingVersion ? badge('草稿 ' + x.editingVersion) : null, x.reviewingVersion ? badge('审核中 ' + x.reviewingVersion) : null) : state ? badge(M.label(state)) : null), actions);
  }
  function connected() {
    const items = [...(model.state.installations || []), ...(model.state.connections || [])].filter(x => !typeFilter || typeOf(x) === typeFilter);
    const filter = h('div', {class: 'filter-tabs', role: 'group', 'aria-label': '资源类型'}, [['', '全部'], ['skill', '技能'], ['mcp', '工具服务'], ['agent', '远端 Agent']].map(([value, text]) => {
      const b = button(text, () => { typeFilter = value; render(); }, {kind: 'quiet'}); b.setAttribute('aria-pressed', String(typeFilter === value)); return b;
    }));
    add($('#main'), h('h2', {tabindex: '-1'}, '已接入的资源'), filter, h('div', {class: 'busy-label'}),
      items.length ? items.map(x => resourceRow(x)) : empty('当前没有匹配的接入记录，可前往发现资源。'));
  }
  function more(trigger, x, view) {
    lastTrigger = trigger; const type = typeOf(x), task = currentTasks(x).at(-1);
    const handlers = {overview: () => openResource(x, view), versions: () => versions(x), local: enterLocal,
      verify: () => verify(x), update: () => install(x), remove: () => remove(x, trigger), tools: () => tools(x), probe: () => probe(x),
      connect: () => connect(x), compose: () => compose(x), task: () => taskView(x, task)};
    U.menu(trigger, M.menu(type, view).map(([key, label]) => ({label, danger: key === 'remove', run: handlers[key],
      disabled: key === 'task' && !task, reason: key === 'task' && !task ? '没有当前上下文中的有效任务引用。' : undefined})));
  }
  function discover() {
    const s = model.search;
    const f = form([field('搜索资源名称（可选）', 'query', s.query, {placeholder: '留空查看全部可见资源'}),
      select('类型', 'type', [['', '全部类型'], ['skill', '技能'], ['mcp', '工具服务'], ['agent', '远端 Agent']], s.type)], '搜索', async data => {
      s.query = data.get('query').trim(); s.type = data.get('type'); await searchPage(false);
    }, s, null, {className: 'search-form'});
    add($('#main'), h('h2', {tabindex: '-1'}, '发现资源'), f);
    if (s.loading) add($('#main'), h('p', {role: 'status'}, '正在搜索…'));
    if (s.error) add($('#main'), h('p', {class: 'error'}, s.error), button('重试查询', () => searchPage(false)));
    add($('#main'), s.items.length ? s.items.map(x => resourceRow(x, 'discover')) : !s.error && !s.loading && s.submitted ? empty('没有匹配的可见资源。') : null);
    if (s.cursor) add($('#main'), h('div', {class: 'list-footer'}, button(s.loading ? '正在加载…' : '加载更多', () => searchPage(true), {disabled: s.loading})));
  }
  async function searchPage(more) {
    const args = model.searchRequest(more); if (!args) return;
    const s = model.search, ticket = model.begin('search');
    s.loading = true; s.submitted = true; s.error = null;
    if (!more) { s.cursor = null; s.applied = {query: args.query, type: args.resourceTypes?.[0] || ''}; }
    if (model.view === 'discover' && !model.subpage) render();
    try {
      const response = await call('search', args);
      if (!model.accepts('search', ticket)) return;
      s.items = M.append(more ? s.items : [], response.result?.items || []); s.cursor = response.result?.nextCursor || null; s.submitted = true;
    } catch (error) { if (model.accepts('search', ticket)) s.error = readable(error); }
    finally { if (model.accepts('search', ticket)) { s.loading = false; if (model.view === 'discover' && !model.subpage) render(); } }
  }
  function owned() {
    const s = model.owned;
    add($('#main'), h('div', {class: 'toolbar'}, h('div', {class: 'title-block'}, h('h2', {tabindex: '-1'}, '我的技能'),
      s.owner ? h('p', {class: 'metadata'}, `当前所有者：${s.owner}`) : null), button('本地技能', enterLocal)));
    if (!scope('develop')) { add($('#main'), empty('尚未启用开发范围。所有权需由 Nacos 管理身份核验。'), button('配置管理身份', enterSettings)); return; }
    add($('#main'), form([field('筛选名称', 'query', s.query, {placeholder: '输入技能名称'})], '查询', data => { s.query = data.get('query'); return ownedPage(1); }, s, null, {className: 'search-form owned-search'}));
    if (s.error) { add($('#main'), h('p', {class: 'error'}, s.error), button('重试读取', () => ownedPage(s.page))); return; }
    if (!s.loaded) { add($('#main'), empty('正在读取当前身份的资源…')); return; }
    add($('#main'),
      s.items.length ? s.items.map(x => resourceRow({...x, resourceType: 'skill'}, 'owned')) : empty('没有归当前身份所有的技能。'),
      h('div', {class: 'pagination'}, h('span', {class: 'metadata'}, `共 ${s.total} 项 · 第 ${s.page} 页`), button('上一页', () => ownedPage(s.page - 1), {disabled: s.page <= 1}), button('下一页', () => ownedPage(s.page + 1), {disabled: !s.hasMore})));
  }
  async function ownedPage(page) {
    const ticket = model.begin('owned'), s = model.owned;
    try { const value = await call('my_skills', {query: s.query, page, limit: 20}); if (model.accepts('owned', ticket)) Object.assign(s, value, {loaded: true, error: null}); }
    catch (error) { if (model.accepts('owned', ticket)) s.error = readable(error); }
    if (model.view === 'owned' && !model.subpage) render();
  }
  async function openResource(x, view = model.view) {
    if (view === 'owned') return versions(x, 'overview');
    if (view === 'discover') {
      const matches = M.connectedMatches(x, model.state);
      if (matches.length === 1) x = {...x, ...matches[0]};
    }
    const d = {kind: 'overview', resource: x, view};
    setDetail(d, false);
    if (typeOf(x) !== 'skill') {
      d.loading = true; renderDetail();
      try { d.found = await call('discover', {resourceType: typeOf(x), name: nameOf(x), ...(versionOf(x) ? {version: versionOf(x)} : {})}); }
      catch (error) { d.error = readable(error); }
      d.loading = false; if (model.detail === d) renderDetail();
    }
  }
  function renderDetail() {
    const box = $('#detail'); box.replaceChildren(); const d = model.detail;
    for (const row of document.querySelectorAll('[data-resource]')) row.classList.toggle('selected', !!d?.resource &&
      (row.dataset.resource === M.identity(d.resource) || !!d.resource.id && row.dataset.connections?.split(',').includes(d.resource.id)));
    $('#layout').classList.toggle('has-detail', !!d && !model.subpage); if (!d || model.subpage) return;
    const type = typeOf(d.resource || {}), subtitle = d.view === 'owned' || d.kind === 'versions' || ['submit', 'publish'].includes(d.plan?.kind || d.action) ? '版本与发布' : type === 'mcp' ? '工具服务' : type === 'agent' ? '能力与任务' : '技能详情';
    add(box, h('div', {class: 'detail-heading'}, h('h2', {tabindex: '-1'}, nameOf(d.resource || {})), h('p', {class: 'metadata'}, subtitle)),
      backButton(), h('div', {class: 'busy-label'}));
    detailTabs(d, box);
    const body = h('div', {class: 'detail-body', 'data-state': d.kind}); add(box, body);
    ({overview: overviewDetail, install: installDetail, connect: connectDetail, plan: planDetail, conflict: conflictDetail,
      result: resultDetail, tools: toolsDetail, probe: probeDetail, compose: composeDetail, task: taskDetail, versions: versionsDetail,
      handoff: handoffDetail, loading: () => add(body, empty('正在读取…'))})[d.kind]?.(d, body);
    locks();
  }
  function detailTabs(d, box) {
    const x = d.resource, type = typeOf(x), connection = connectionOf(x);
    if (d.action === 'disconnect') return;
    let items, selected;
    if (d.kind === 'versions') {
      items = [['overview', '概览', () => { d.section = 'overview'; renderDetail(); }], ['versions', '版本与发布', () => { d.section = 'versions'; renderDetail(); }]];
      selected = d.section;
    } else if (type === 'mcp') {
      items = [['overview', '概览', () => openResource(x)], ['tools', '工具', () => tools(connection || x)], ['connect', '连接', () => connect(connection || x)]];
      selected = ['tools', 'handoff'].includes(d.kind) ? 'tools' : d.kind === 'overview' ? 'overview' : 'connect';
    } else if (type === 'agent') {
      items = [['overview', '概览', () => openResource(x)], ['compose', '发起任务', () => compose(connection)],
        ['task', '当前任务', () => taskView(connection, currentTasks(connection).at(-1))]];
      selected = ['compose', 'task'].includes(d.kind) ? d.kind : 'overview';
    }
    if (!items) return;
    add(box, h('nav', {class: 'detail-tabs', 'aria-label': '资源详情分区'}, items.map(([key, text, run]) => {
      const disabled = type === 'agent' && key !== 'overview' && (!connection || key === 'task' && (!currentTasks(connection).length || d.kind === 'task' && !d.task && ['failed', 'result_unknown'].includes(d.value?.status)));
      const b = button(text, run, {kind: 'quiet', disabled, reason: disabled ? '请先接入服务并取得有效任务记录。' : undefined});
      b.setAttribute('aria-current', key === selected ? 'page' : 'false'); return b;
    })));
  }
  function overviewDetail(d, box) {
    const x = d.resource, type = typeOf(x);
    add(box, h('h3', {}, type === 'agent' ? '能力概览' : '资源概览'), h('p', {}, d.found?.description || x.description || x.summary || '暂无资源描述。'),
      kv([['版本', d.found?.version || versionOf(x) || '接入前解析'], ['来源', x.ref ? `${x.ref.registryId} / ${x.ref.namespaceId}` : model.state.profile.namespaceId], ['安装位置', x.target],
        ['服务地址', x.endpoint?.url || d.found?.endpoints?.map(e => e.url).join('\n')], ['协议', type === 'mcp' ? 'Streamable HTTP' : type === 'agent' ? 'A2A 0.3.0 / JSON-RPC' : null], ['当前状态', M.label(x.loadState || x.status)]]));
    if (d.loading) add(box, h('p', {role: 'status', class: 'muted'}, '正在读取注册信息…'));
    if (d.error) add(box, U.summary('无法读取注册信息', d.error, 'bad'), button('重试读取', () => openResource(x)));
    if (type === 'agent') add(box, U.summary('支持文本任务', '当前适配支持文本发送、状态查询和请求取消，不提供文件或流式回复。'));
    if (type === 'skill' && x.id) add(box, U.summary('文件已安装', '是否已被当前 Codex 对话加载，需要单独确认。'));
    const actions = U.actions();
    if (type === 'skill') {
      if (x.id) {
        add(actions, handoffButton(x, 'primary'), button('检查文件与访问', () => verify(x)),
          actionButton('检查更新', () => install(x), 'install'));
        add(box, h('p', {class: 'muted', 'data-handoff-hint': true, hidden: canHandoff()},
          NacosBuild.entrypoint === 'global' ? '当前是全局页面。要直接使用，请回到目标对话，让 Codex 在该对话侧栏打开资源中心。此处可复制使用说明。'
            : '当前应用未提供对话消息能力；此处可复制使用说明。'));
      } else add(actions, actionButton('安装技能', () => install(x), 'install', 'primary'));
    } else {
      const configure = actionButton(x.id ? type === 'agent' ? '编辑接入设置' : '配置连接' : type === 'mcp' ? '连接工具' : '接入 Agent', () => connect(x), 'call', 'primary');
      if (d.error || d.loading) { configure.dataset.blocked = 'true'; configure.disabled = true; }
      add(actions, configure);
      if (x.id) add(actions, button(type === 'mcp' ? '查看工具' : '发起任务', () => type === 'mcp' ? tools(x) : compose(x)));
    }
    add(box, actions, raw(x));
  }
  function install(x) { setDetail({kind: 'install', resource: x, draft: {version: x.id ? '' : versionOf(x) || '', root: x.target ? model.state.profile.installRoots.find(r => x.target.startsWith(r + '/')) : model.state.profile.installRoots[0] || ''}}); }
  function installDetail(d, box) {
    const roots = model.state.profile.installRoots || [];
    if (!roots.length) { add(box, empty('需要先添加一个合法安装目录。'), button('添加安装目录', () => { preferences.selectGroup('directories'); enterSettings(); })); return; }
    add(box, h('h3', {class: 'step-title'}, d.resource.id ? '选择更新版本' : '选择安装目标'), form([
      select('完整安装目录', 'root', roots.map(x => [x, x]), d.draft.root), field('指定版本（留空解析默认版本）', 'version', d.draft.version)],
      '查看安装变更', async data => {
        const args = {name: nameOf(d.resource), installRoot: data.get('root'), ...(data.get('version') ? {version: data.get('version')} : {})};
        await prepare('install_plan', args, d);
      }, d.draft, 'install'));
  }
  async function prepare(action, args, source) {
    try { const plan = await mutation(action, args); if (model.detail === source || model.subpage === 'upload') setDetail({kind: 'plan', resource: source.resource, plan, source}); }
    catch (error) {
      if (error.kind === 'conflict' && model.detail === source) setDetail({kind: 'conflict', resource: source.resource, conflict: error.value?.conflict, error: readable(error), source, retry: () => prepare(action, args, source)});
      else throw error;
    }
  }
  function changes(value) {
    if (!value) return null;
    return h('div', {}, h('p', {}, `新增 ${(value.added || []).length} 个 · 修改 ${(value.modified || []).length} 个 · 删除 ${(value.removed || []).length} 个`),
      h('ul', {class: 'file-list'}, ['added', 'modified', 'removed'].flatMap(key => (value[key] || []).map(path => h('li', {}, ({added: '新增', modified: '修改', removed: '删除'})[key] + ' · ' + path)))));
  }
  function planDetail(d, box) {
    const p = d.plan, labels = {install: d.resource.id ? '更新技能' : '安装技能', mcp_config: '保存工具连接', bind_agent: d.resource.id ? '保存接入设置' : '确认接入', submit: '提交版本', publish: '发布版本'};
    add(box, h('h3', {class: 'step-title'}, p.kind === 'submit' ? '确认提交版本' : p.kind === 'publish' ? '确认发布版本' : p.kind === 'install' && d.resource.id ? '核对更新' : '核对变更'), kv([['实际版本', p.version || p.targetVersion], ['安装目标', p.target], ['连接目标', p.endpoint?.url], ['配置位置', p.configPath], ['可见性', visibility(p.visibility)]]),
      changes(p.changes), p.kind === 'bind_agent' ? h('p', {}, '仅保存服务绑定，不发送任务。') : null,
      p.kind === 'submit' ? h('p', {}, '有匹配流程时进入审核；没有匹配流程时可能直接上线。') : null,
      U.actions(button('返回修改', () => { model.returnTo(d.source); renderDetail(); }),
        actionButton(d.attempted ? '此计划已执行，请核对结果' : labels[p.kind] || '确认操作', () => apply(d), null, 'primary')), raw(p));
    if (d.attempted) {
      for (const node of box.querySelectorAll('[data-write]')) { node.disabled = true; node.dataset.blocked = 'true'; }
      add(box, h('p', {class: 'muted'}, '本计划已发出，不能再次执行。请刷新资源或核对待处理操作。'));
    }
  }
  async function apply(d) {
    if (d.attempted) return; d.attempted = true; locks();
    const location = navigationId, sourceDetail = model.detail;
    const stillHere = () => location === navigationId && sourceDetail === model.detail && !model.subpage;
    try {
      const value = await mutation('apply', {planId: d.plan.id});
      const result = {kind: 'result', resource: d.resource, value, action: d.plan.kind, updated: !!d.resource.id};
      if (d.plan.kind === 'mcp_config') toolCache.delete(d.plan.connectionId);
      if (['submit', 'publish'].includes(d.plan.kind)) {
        model.owned.loaded = false;
        if (stillHere() && model.view === 'owned') await ownedPage(model.owned.page);
      }
      if (stillHere()) { model.detail = result; render(); $('#detail h2')?.focus(); } else { notify('操作已返回，请在对应资源或待处理操作中核对。'); }
    } catch (error) {
      if (stillHere()) { model.detail = {kind: 'result', resource: d.resource, value: {status: ['timeout', 'bridge', 'protocol'].includes(error.kind) ? 'result_unknown' : 'failed', error: {message: readable(error)}}, action: d.plan.kind}; render(); }
    }
  }
  function conflictDetail(d, box) {
    add(box, h('h3', {class: 'step-title'}, '操作尚未执行'), badge('检测到冲突', 'warning'), h('p', {}, d.error),
      d.conflict?.target ? kv([['受影响目录', d.conflict.target]]) : null, changes(d.conflict?.changes), h('p', {}, '请先处理差异，再重新检查。本地文件保持原样，不提供强制覆盖。'),
      U.actions(button('返回修改', () => { model.returnTo(d.source); renderDetail(); }), button('重新检查', () => { model.returnTo(d.source); return d.retry(); })));
  }
  async function remove(x, trigger) {
    const action = typeOf(x) === 'skill' ? 'uninstall_plan' : 'disconnect_plan';
    let plan; const location = navigationId, context = model.context;
    try { plan = await mutation(action, typeOf(x) === 'skill' ? {installationId: x.id} : {connectionId: x.id}); }
    catch (error) { notify(readable(error) + ' 原文件或连接保持不变。', true); return; }
    if (location !== navigationId || context !== model.context || !trigger.isConnected) return;
    U.confirm(trigger, (typeOf(x) === 'skill' ? '卸载 ' : '解除接入 ') + nameOf(x) + '？',
      h('div', {}, kv([['资源', nameOf(x)], ['版本', versionOf(x)], ['目标', x.target || x.configPath || x.endpoint?.url]]),
        h('p', {}, typeOf(x) === 'skill' ? '仅移除未被修改的受管技能文件，保留 Nacos 资源。' : typeOf(x) === 'agent' ? '仅移除本地绑定；远端服务和已发出的任务不会停止。' : '仅移除受管连接配置，保留其他配置与远端服务。Codex 可能仍需刷新。')),
      typeOf(x) === 'skill' ? '确认卸载' : '确认解除接入', async () => { await apply({resource: x, plan}); });
  }
  async function verify(x) {
    const ticket = model.begin('detail'), location = navigationId;
    const value = await call('verify_skill', {installationId: x.id});
    if (!model.accepts('detail', ticket) || location !== navigationId || model.subpage) return;
    setDetail({kind: 'result', resource: x, value, action: 'verify'});
  }
  function resultDetail(d, box) {
    const v = d.value, failure = ['failed', 'result_unknown', 'recovery_required'].includes(v.status), r = v.result || v;
    const title = failure ? M.label(v.status) : ({install: d.updated ? '技能已更新' : '技能已安装', uninstall: '技能已卸载', mcp_config: '连接配置已保存', bind_agent: d.updated ? '接入设置已更新' : 'Agent 已接入', disconnect: '已解除接入', verify: '文件与访问检查通过', submit: r.status === 'reviewing' ? '审核中' : r.status === 'online' ? '版本已发布' : '版本提交结果', publish: '版本已发布'})[d.action] || '操作结果';
    const explanation = failure ? v.error?.message || '无法确认结果，请先核对已有操作，不要重复提交。' : ({
      install: '文件写入完成。仍需确认 Codex 已加载此版本。', verify: '受管文件与远端读取已检查。此次检查不改变 Codex 加载状态。',
      uninstall: '仅移除受管技能文件，Nacos 资源和其他技能保留。', mcp_config: '待 Codex 刷新；尚未验证当前对话加载。连接诊断是下一项独立操作。',
      bind_agent: '服务引用与独立认证已保存，尚未发送任务。', disconnect: typeOf(d.resource) === 'agent' ? '本地绑定已移除。已发送的任务继续按远端状态运行。' : '受管连接已移除。远端服务保留，Codex 可能仍需刷新。',
      submit: r.status === 'reviewing' ? '提交已接受，等待审核。现有线上版本保持不变。' : '服务端已返回提交结果，请按确切版本核对状态。', publish: '选定版本已发布并核验，原资源列表已刷新。'
    })[d.action];
    add(box, U.summary(title, explanation, failure ? 'warning' : 'good'),
      kv([['实际版本', r.version], ['目标', r.target || r.endpoint?.url], ['可见性', visibility(r.visibility)]]));
    const actions = U.actions();
    if (failure) add(actions, button('查看待处理操作', () => { selectedOperation = null; model.enter('operations', scrollY); render(); }));
    if (!failure && ['mcp_config', 'bind_agent'].includes(d.action)) {
      const connection = model.state.connections.find(x => x.ref.name === nameOf(d.resource) && typeOf(x) === typeOf(d.resource));
      if (connection) add(actions, button(typeOf(connection) === 'mcp' ? '检查连接' : '发起任务', () => typeOf(connection) === 'mcp' ? probe(connection) : compose(connection), {kind: 'primary'}));
    }
    if (!failure && d.action === 'install') add(actions, button('查看已接入', () => navigate('connected'), {kind: 'primary'}));
    if (!failure && d.action === 'verify') add(actions, button('返回技能详情', () => openResource(d.resource), {kind: 'primary'}));
    if (!failure && ['uninstall', 'disconnect'].includes(d.action)) add(actions, button('发现其他资源', () => navigate('discover'), {kind: 'primary'}));
    if (!failure && ['submit', 'publish'].includes(d.action)) add(actions, button(d.action === 'submit' ? '刷新版本与审核状态' : '返回版本列表', () => versions(d.resource), {kind: 'primary'}));
    if (v.id || v.operationId) add(actions, button('查看操作记录', () => inspect(v.id || v.operationId), {kind: 'quiet'}));
    add(box, actions, raw(v));
  }
  async function connect(x) {
    const ticket = model.begin('detail'); const view = model.view;
    const found = await call('discover', {resourceType: typeOf(x), name: nameOf(x), ...(versionOf(x) ? {version: versionOf(x)} : {})});
    if (model.accepts('detail', ticket) && view === model.view && !model.subpage) setDetail({kind: 'connect', resource: x, found, draft: {endpoint: '0', auth: x.auth?.type || 'none', tokenEnv: x.auth?.tokenEnv || (typeOf(x) === 'mcp' ? 'NACOS_PLUGIN_MCP_TOKEN' : 'NACOS_PLUGIN_AGENT_TOKEN')}});
  }
  function connectDetail(d, box) {
    const auth = select('独立服务认证', 'auth', [['none', '无需认证'], ['bearer', 'Bearer Token']], d.draft.auth);
    const token = field('Token 环境变量名', 'tokenEnv', d.draft.tokenEnv);
    token.hidden = d.draft.auth !== 'bearer'; auth.querySelector('select').onchange = e => { d.draft.auth = e.target.value; token.hidden = e.target.value !== 'bearer'; token.querySelector('input').required = !token.hidden; };
    add(box, h('h3', {class: 'step-title'}, '连接设置'), h('p', {}, '地址来自注册信息。仅引用独立凭据，不在页面填写秘密。'), form([
      d.found.endpoints.length === 1 ? h('div', {}, kv([['注册端点（只读）', d.found.endpoints[0].url]]), h('input', {type: 'hidden', name: 'endpoint', value: '0'})) : select('注册端点', 'endpoint', d.found.endpoints.map((e, i) => [String(i), e.url]), d.draft.endpoint), auth, token,
      typeOf(d.resource) === 'agent' ? h('p', {}, 'A2A 0.3.0 / JSON-RPC。保存绑定不会发送任务。') : h('div', {}, kv([['配置目标', model.state.profile.codexConfig || '尚未配置']]), h('p', {}, '仅修改受管连接，保留其他 Codex 配置。'))],
      '核对连接变更', data => prepare('connection_plan', {resourceType: typeOf(d.resource), name: nameOf(d.resource), endpointIndex: Number(data.get('endpoint')),
        ...(d.found.version ? {version: d.found.version} : {}), auth: data.get('auth') === 'none' ? {type: 'none'} : {type: 'bearer', tokenEnv: data.get('tokenEnv')}}, d), d.draft, 'call'));
  }
  function tools(x) { setDetail({kind: 'tools', resource: x, value: toolCache.get(x.id)}, false); }
  async function probe(x) {
    const d = {kind: 'probe', resource: x, loading: true}; setDetail(d);
    const ticket = model.begin('detail'), location = navigationId;
    try { d.value = await call('mcp_probe', {connectionId: x.id}); toolCache.set(x.id, d.value); }
    catch (error) { d.error = readable(error); }
    d.loading = false;
    if (model.accepts('detail', ticket) && location === navigationId && model.detail === d) renderDetail();
  }
  function probeDetail(d, box) {
    add(box, U.summary(d.loading ? '正在检查连接…' : d.error ? '连接诊断失败' : '连接诊断通过',
      d.loading ? '正在验证服务认证并读取工具列表。' : d.error || `认证与工具发现通过，共 ${d.value.tools?.length || 0} 个工具。`, d.error ? 'bad' : d.loading ? '' : 'good'),
      h('p', {class: 'muted'}, '未调用业务工具。当前对话是否已加载，需要单独核验。'));
    if (!d.loading) add(box, U.actions(button(d.error ? '重新诊断' : '查看工具', () => d.error ? probe(d.resource) : tools(d.resource), {kind: 'primary'})));
  }
  function toolsDetail(d, box) {
    if (!d.resource.id) {
      add(box, U.summary('尚未接入', '先配置服务连接，再读取可用工具。'), U.actions(button('配置连接', () => connect(d.resource), {kind: 'primary'}))); return;
    }
    if (!d.value) add(box, empty('尚未读取工具列表。'), U.actions(button('检查连接并读取工具', () => probe(d.resource), {kind: 'primary'})));
    else {
      add(box, h('h3', {}, '已发现工具'), !d.value.tools?.length ? empty('服务返回零个工具。') : d.value.tools.map(t => h('section', {class: 'tool-item'}, h('h3', {}, t.name), h('p', {}, t.description || '暂无说明'),
        h('details', {}, h('summary', {}, '输入参数'), kv(Object.entries(t.inputSchema?.properties || {}).map(([key, value]) => [key, `${value.type || '结构化值'}${t.inputSchema?.required?.includes(key) ? ' · 必填' : ''} · ${value.description || ''}`]))))),
        h('p', {class: 'muted'}, '工具已发现；当前对话加载与业务调用仍需分别确认。'),
        U.actions(handoffButton(d.resource, 'primary'), button('重新诊断', () => probe(d.resource))));
    }
  }
  function compose(x) { setDetail({kind: 'compose', resource: x, draft: {text: ''}}); }
  function composeDetail(d, box) {
    add(box, h('h3', {class: 'step-title'}, '发起任务'), kv([['接收目标', d.resource.endpoint?.url]]), form([
      field('任务内容', 'text', d.draft.text, {multiline: true, required: true, maxlength: 65536}), h('p', {class: 'muted'}, '只发送上方文本，不自动附加对话或文件。')], '发送任务', async data => {
      const value = await mutation('agent_send', {connectionId: d.resource.id, text: data.get('text')});
      if (model.detail === d) setDetail({kind: 'task', resource: d.resource, value, task: model.state.tasks.find(t => t.taskHandle === value.taskHandle), draft: d.draft});
    }, d.draft, 'call'));
  }
  function taskView(x, task) { setDetail({kind: 'task', resource: x, task}); }
  function taskDetail(d, box) {
    const r = d.value?.result, task = model.state.tasks?.find(t => t.taskHandle === d.task?.taskHandle) || d.task;
    const uncertain = ['failed', 'result_unknown'].includes(d.value?.status);
    const status = task?.status, cancelPending = task?.cancelRequested && !M.terminal(status);
    const title = uncertain ? '无法确认发送结果' : cancelPending ? '取消请求已发送' : ({completed: '任务已完成', canceled: '任务已取消', failed: '任务失败', rejected: '任务被拒绝'})[status] || (task ? '任务运行中' : r?.kind === 'message' ? '已收到回复' : '没有当前任务');
    const description = uncertain ? '请求可能已生效。保留原输入与目标，先核对操作记录，不直接重发。' : cancelPending ? '尚未确认停止，远端可能仍在处理。查询不会再次发送取消请求。' : status === 'canceled' ? '服务已确认取消。这不会撤销任务先前产生的远端效果。' : task && !M.terminal(status) ? '已取得有效任务引用。查询状态不会重新发送任务。' : '';
    add(box, U.summary(title, description, uncertain || cancelPending ? 'warning' : M.terminal(status) || r?.kind === 'message' ? 'good' : ''),
      kv([['接收目标', d.resource.endpoint?.url], ['最近核验', task?.updatedAt ? new Date(task.updatedAt * 1000).toLocaleString() : null]]));
    if (uncertain && d.draft?.text) add(box, h('section', {class: 'task-input-summary'}, h('h3', {}, '原任务内容'), h('p', {class: 'task-text'}, d.draft.text)));
    const parts = r?.kind === 'message' ? r.parts : [...(r?.status?.message?.parts || []), ...(r?.artifacts || []).flatMap(a => a.parts || [])];
    for (const part of parts || []) add(box, part.kind === 'text' ? h('p', {class: 'task-text'}, part.text) : h('p', {class: 'muted'}, '包含当前页面未支持的非文本结果，见诊断详情。'));
    const actions = U.actions();
    if (task && !M.terminal(status)) add(actions, button('查询状态', () => updateTask(d, task, 'get'), {kind: 'primary'}));
    if (M.canCancel(task)) add(actions, actionButton('请求取消', () => updateTask(d, task, 'cancel'), 'call'));
    if (M.terminal(status) || r?.kind === 'message') add(actions, button('返回任务输入', () => compose(d.resource), {kind: 'primary'}));
    if (!task && !r) add(box, h('p', {class: 'muted'}, '没有有效任务引用，无法查询或取消。'));
    if (uncertain) add(actions, button('返回能力说明', () => openResource(d.resource)));
    if (d.value?.operationId || d.value?.id) add(actions, button('查看操作记录', () => inspect(d.value.operationId || d.value.id), {kind: 'quiet'}));
    add(box, actions); if (d.value) add(box, raw(d.value));
  }
  async function updateTask(d, task, action) {
    const value = await mutation('agent_task', {taskHandle: task.taskHandle, action});
    d.value = value; d.task = model.state.tasks.find(t => t.taskHandle === task.taskHandle); if (model.detail === d) renderDetail();
  }
  async function versions(x, section = 'versions') {
    const ticket = model.begin('detail'), view = model.view;
    const value = await call('skill_status', {name: nameOf(x)});
    if (model.accepts('detail', ticket) && model.view === view && !model.subpage) setDetail({kind: 'versions', resource: x, value, section,
      selectedVersion: value.metadata.editingVersion || value.metadata.reviewingVersion || value.metadata.versions?.[0]?.version}, false);
  }
  function versionsDetail(d, box) {
    const meta = d.value.metadata;
    if (d.section === 'overview') {
      add(box, h('h3', {}, '维护者概览'), h('p', {}, meta.description || d.resource.description || '暂无资源描述。'),
        kv([['可见性', visibility(meta.scope)], ['已发布', meta.labels?.latest], ['草稿', meta.editingVersion], ['审核中', meta.reviewingVersion]]),
        U.actions(button('查看版本与发布', () => { d.section = 'versions'; renderDetail(); }, {kind: 'primary'}))); return;
    }
    add(box, h('p', {class: 'metadata'}, '可见性：' + visibility(meta.scope)),
      h('div', {class: 'version-list', role: 'radiogroup', 'aria-label': '选择版本'}, (meta.versions || []).map(v => {
        const input = h('input', {type: 'radio', name: 'resourceVersion', value: v.version, checked: v.version === d.selectedVersion,
          onchange: () => { d.selectedVersion = v.version; renderDetail(); $('#detail input[name=resourceVersion]:checked')?.focus(); }});
        return h('label', {class: 'version-choice'}, input, h('strong', {}, v.version), badge(M.canPublish(v) ? '审核通过' : M.label(v.status)));
      })));
    const v = (meta.versions || []).find(v => v.version === d.selectedVersion);
    if (!v) { add(box, empty('暂无可读取的版本。')); return; }
    const writable = d.resource.writable !== false && scope('publish');
    const explanation = {draft: '已保存，尚未提交。', online: '这是已发布版本。新草稿不会改变线上内容。', reviewing: '等待审核完成；当前线上版本保持不变。', reviewed: M.canPublish(v) ? '审核通过，可继续核对并发布此版本。' : '审核已完成，但没有通过证据，不能发布。'}[v.status] || '请核对服务端返回的版本状态。';
    const panel = h('section', {class: 'version-detail'}, U.summary(M.canPublish(v) ? '审核通过' : M.label(v.status), explanation));
    const actions = U.actions();
    if (['draft', 'reviewed'].includes(v.status) && !writable) add(panel, U.summary('当前身份没有发布权限', '请核对管理身份与服务端授权。现有版本保持可读。', 'warning'));
    if (v.status === 'draft' || M.canPublish(v)) {
      const submit = actionButton(v.status === 'draft' ? '提交版本' : '发布版本', () => lifecycle(d, v, v.status === 'draft' ? 'submit' : 'publish'), 'publish', 'primary');
      if (!writable) { submit.dataset.blocked = 'true'; submit.disabled = true; }
      add(actions, submit);
    }
    if (!writable) add(actions, button('配置管理身份', enterSettings));
    add(actions, button('刷新版本与审核状态', () => versions(d.resource), {kind: 'quiet'}));
    add(panel, actions, raw(v)); add(box, panel);
  }
  function lifecycle(d, version, action) {
    return prepare('publish_plan', {name: nameOf(d.resource), version: version.version, action}, d);
  }
  async function handoff(x) {
    if (handoffPending) return;
    const text = `请使用 Nacos 资源「${nameOf(x)}」（${M.types[typeOf(x)]}，版本 ${versionOf(x) || '待解析'}，来源 ${x.ref?.registryId || model.state.profile.id} / ${x.ref?.namespaceId || model.state.profile.namespaceId}）。${x.target ? `安装位置：${x.target}。` : ''}先核验接入与当前权限，再完成当前对话中的任务。`;
    const d = {kind: 'handoff', resource: x, sent: false, text, pending: canHandoff()};
    handoffPending = d.pending; setDetail(d); updateHandoffButtons();
    if (!d.pending) return;
    try { await bridge.messageCurrentConversation(text); d.sent = true; }
    catch (error) {
      d.error = error.kind === 'timeout'
        ? '发送结果尚未确认，请先查看目标对话，避免重复发送。'
        : '未能发送到当前对话。请核对页面的对话入口，或复制下方使用说明。';
    } finally {
      d.pending = false; handoffPending = false;
      if (model.detail === d) renderDetail();
      updateHandoffButtons();
    }
  }
  function handoffDetail(d, box) {
    add(box, h('h3', {class: 'step-title'}, d.pending ? '正在发送到当前对话…' : d.error ? '未确认交接' : d.sent ? '已发送到当前对话' : '复制使用说明'),
      h('p', {role: 'status'}, d.pending ? '正在等待应用确认，请勿重复发送。' : d.error || (d.sent ? '使用说明已交给当前对话；资源是否已加载，需要在对话中核验。' : '此页面无法直接发送到当前对话。可复制下方说明，或在目标对话中打开资源中心侧栏。')),
      field('使用说明', 'instructions', d.text, {multiline: true, readonly: true}), button('复制说明', async () => {
        try { await navigator.clipboard.writeText(d.text); notify('已复制使用说明。'); } catch { notify('剪贴板不可用，请选中上方文本复制。'); }
      }));
  }
  function settings() { preferences.render($('#main')); }
  function localSkills() {
    const main = $('#main'), scan = model.state.scan, roots = model.state.profile.scanRoots;
    const backLabel = model.origin?.subpage === 'settings' ? '返回设置' : model.origin?.view === 'owned' ? '返回我的资源' : '返回资源中心';
    add(main, U.subpage('本地技能', backLabel, leaveSubpage),
      h('section', {class: 'scan-summary', 'aria-label': '扫描范围'},
        h('div', {class: 'scan-info'}, h('div', {class: 'scan-roots'}, h('span', {}, '扫描目录'),
          roots.length ? roots.map(root => h('span', {class: 'path-text'}, root)) : h('span', {}, '尚未配置')),
          h('p', {class: 'metadata'}, scan ? `已扫描 ${scan.items.length} 项。本次扫描只读取技能信息，不上传文件。` : '扫描已选目录中的技能信息，不执行技能，也不上传文件。')),
        h('div', {class: 'scan-actions'},
          actionButton(scan ? '重新扫描' : '扫描所选目录', async () => { await mutation('scan', {}); localSelection.clear(); localResults = null; upload = null; if (model.subpage === 'local') render(); }),
          button(roots.length ? '调整目录' : '添加目录', () => { preferences.selectGroup('directories', true); enterSettings(); }, {kind: 'quiet'}))));
    if (!scan) { add(main, empty('尚未扫描。列表中的资源不会被自动选择。'), U.actions(actionButton('暂时跳过', async () => { await mutation('onboarding', {action: 'skip'}); leaveSubpage(); }))); return; }
    const batch = h('div', {class: 'batch-actions'}), count = h('span', {class: 'selection-count', role: 'status'});
    const updateBatch = () => { count.textContent = `已选 ${localSelection.size} 项`; for (const b of batch.querySelectorAll('.batch-buttons [data-write]')) { b.dataset.blocked = String(!localSelection.size); b.disabled = !localSelection.size || !!model.busy.size; } };
    async function choose(action) {
      localResults = await mutation('select', {scanId: scan.id, selections: [...localSelection].map(candidateId => ({candidateId, action}))});
      localSelection.clear(); if (model.subpage === 'local') render();
    }
    add(batch, count, h('div', {class: 'batch-buttons'}, actionButton('仅跟踪选中项', () => choose('track')), actionButton('忽略选中项', () => choose('ignore'))));
    const list = h('div', {class: 'local-list', 'aria-label': '本地技能扫描结果'}); add(main, list);
    for (const item of scan.items) {
      const binding = model.state.bindings.find(x => x.path === item.path), result = localResults?.results?.find(x => x.candidateId === item.id);
      const itemName = item.name || (item.path || item.root).split('/').filter(Boolean).at(-1);
      const chooseBox = check(itemName, 'candidate-' + item.id, localSelection.has(item.id)), input = chooseBox.querySelector('input');
      chooseBox.classList.add('local-select');
      input.disabled = item.status !== 'candidate'; input.onchange = () => { input.checked ? localSelection.add(item.id) : localSelection.delete(item.id); updateBatch(); };
      add(list, h('article', {class: 'local-row'},
        h('div', {class: 'local-info'}, chooseBox, h('div', {class: 'local-content'},
          item.description ? h('p', {class: 'local-description'}, item.description) : null,
          h('p', {class: 'metadata path-text'}, item.path || item.root),
          h('div', {class: 'row-badges'}, badge(M.label(result?.status || result?.error || binding?.policy || item.status)),
            item.reason ? h('span', {class: 'error'}, ({validation: '技能信息不完整或格式不正确', filesystem: '无法读取文件，请检查目录权限', permission: '该目录不在允许范围内'})[item.reason] || '无法读取技能信息') : null))),
        h('div', {class: 'local-actions'}, item.status === 'candidate' ? actionButton('准备上传', () => previewUpload(scan.id, item.id), 'develop') : null)));
    }
    if (!scan.items.length) add(list, empty('已选目录中没有找到技能。可调整目录后重新扫描。'));
    if (localResults) {
      const results = localResults.results || [];
      add(main, h('p', {class: 'local-feedback', role: 'status'}, `已处理 ${results.length} 项，请查看各行结果。${results.some(r => r.error) ? '部分项目未完成，未成功的项目保持原状。' : '未上传任何文件。'}`));
    }
    updateBatch();
    add(main, batch);
    const finish = actionButton('完成盘点', async () => { await mutation('onboarding', {action: 'finish'}); leaveSubpage(); }, null, 'quiet finish-scan');
    add(batch, finish);
  }
  async function previewUpload(scanId, candidateId) {
    const context = model.context, preview = await call('upload_preview', {scanId, candidateId});
    if (context !== model.context || model.subpage !== 'local') return;
    upload = {preview, args: {scanId, candidateId, expectedContentHash: preview.contentHash}, stage: 'preview', draft: {}, conflict: null};
    model.enter('upload', scrollY); render(); scrollTo(0, 0);
  }
  async function uploadPlan() {
    const u = upload; u.error = null;
    try {
      const plan = await mutation('upload_plan', {...u.args, bindExisting: u.draft.bindExisting === true, overwriteDraft: u.draft.overwriteDraft === true, commitMessage: u.draft.commitMessage || ''});
      if (upload === u) { u.plan = plan; u.stage = 'confirm'; u.conflict = null; }
    } catch (error) {
      if (upload !== u) return;
      if (error.value?.conflict) { u.conflict = {...u.conflict, ...error.value.conflict}; u.stage = 'conflict'; }
      else u.error = readable(error);
    }
    if (model.subpage === 'upload' && upload === u) render();
  }
  function uploadPage() {
    const main = $('#main'), u = upload;
    if (!u) { leaveSubpage(); return; }
    const titles = {preview: '准备上传', conflict: '处理草稿冲突', confirm: u.plan?.action === 'OVERWRITE_DRAFT' ? '核对覆盖草稿变更' : '核对草稿变更', result: u.result?.status === 'completed' ? '草稿已保存' : '保存结果待核对'};
    add(main, U.subpage(titles[u.stage], '返回本地技能', leaveSubpage));
    const content = h('div', {class: 'flow-content', 'data-state': 'upload-' + u.stage}); add(main, content);
    add(content, h('ol', {class: 'flow-steps', 'aria-label': '上传步骤'}, ['核对文件', '预检并确认', '保存结果'].map((text, index) =>
      h('li', {'aria-current': index === (u.stage === 'preview' ? 0 : u.stage === 'result' ? 2 : 1) ? 'step' : null}, `${index + 1} ${text}`))),
      h('h3', {}, u.preview.name));
    if (u.stage === 'result') {
      const complete = u.result.status === 'completed', result = u.result.result || {};
      add(content, U.summary(complete ? `草稿 ${result.version || u.plan.targetVersion} 已保存` : M.label(u.result.status), complete ? '保存结果已核验，尚未提交或发布。' : '请求可能已生效。没有可靠证据前保留未知状态，不重复提交。', complete ? 'good' : 'warning'),
        kv([['实际版本', result.version], ['命名空间', u.preview.namespaceId], ['可见性', visibility(result.visibility)]]),
        U.actions(button('返回本地技能', leaveSubpage), complete ? button('查看我的资源', () => { navigate('owned'); return ownedPage(1); }, {kind: 'primary'}) : button('核对操作记录', () => inspect(u.result.id), {kind: 'primary'})), raw(u.result)); return;
    }
    add(content, h('section', {class: 'flow-facts'}, kv([['目标', `${model.state.profile.displayName || model.state.profile.id} / ${u.preview.namespaceId}`], ['来源目录', u.preview.path], ['上传地址', u.preview.destination],
      ...(u.stage === 'preview' ? [['文件总量', `${u.preview.files.length} 个 · ${u.preview.files.reduce((n, x) => n + x.bytes, 0).toLocaleString()} 字节`]] : [])])));
    if (u.stage === 'preview') add(content,
      h('ul', {class: 'file-table', 'aria-label': '待上传文件'}, u.preview.files.map(x => h('li', {}, h('span', {}, x.path), h('span', {}, `${x.bytes.toLocaleString()} 字节`)))),
      form([field('变更说明（可选）', 'commitMessage', u.draft.commitMessage || '', {multiline: true}),
        h('p', {class: 'muted'}, '下一步将这些文件发送到管理接口预检，尚不保存草稿。')], '发送并预检', uploadPlan, u.draft, 'develop'));
    if (u.stage === 'conflict') {
      const c = u.conflict;
      const consent = h('p', {class: 'muted', role: 'status'});
      const updateConsent = () => { consent.textContent = u.draft.bindExisting && u.draft.overwriteDraft ? '已选择绑定与覆盖，尚未重新预检。' : u.draft.bindExisting ? '已选择同名绑定，尚未授权覆盖草稿。' : u.draft.overwriteDraft ? '已选择覆盖草稿，尚未确认同名绑定。' : '预检发现冲突，尚未保存。请分别确认需要的操作。'; };
      updateConsent();
      add(content, U.summary('需要明确处理同名资源与草稿', '目标或内容变化后需要重新预检。选择不会立即覆盖文件。', 'warning'),
        kv([['已有资源', c.name], ['已有草稿', c.draftVersion]]));
      const f = form([c.requiresBind ? check('绑定经核验的同名资源', 'bindExisting', u.draft.bindExisting === true) : null,
        c.requiresOverwrite ? check('允许覆盖上述远端草稿', 'overwriteDraft', u.draft.overwriteDraft === true) : null, consent], '重新预检', async () => {
          if (c.requiresBind && !u.draft.bindExisting || c.requiresOverwrite && !u.draft.overwriteDraft) throw new Error('请分别选择要授权的操作，或返回本地技能。');
          await uploadPlan();
        }, u.draft, 'develop', {back: button('返回文件预览', () => { u.stage = 'preview'; render(); })});
      f.addEventListener('change', updateConsent); add(content, f);
    }
    if (u.stage === 'confirm') add(content, U.summary('可以保存草稿', u.plan.action === 'OVERWRITE_DRAFT' ? '将覆盖已核验的远端草稿，不修改已发布版本。' : '预检完成，尚未保存草稿。', u.plan.action === 'OVERWRITE_DRAFT' ? 'warning' : ''),
      kv([['预检版本', u.plan.targetVersion], ['可见性', visibility(u.plan.visibility)]]), changes(u.plan.changes),
      h('p', {class: 'muted'}, '文件与目标变化时，返回文件预览重新确认。'),
      U.actions(button('返回文件预览', () => { u.stage = 'preview'; u.plan = null; render(); }), actionButton('保存草稿', async () => {
        if (u.attempted) return; u.attempted = true;
        try { u.result = await mutation('apply', {planId: u.plan.id}); }
        catch (error) { u.result = {status: 'result_unknown', error: {message: readable(error)}}; }
        u.stage = 'result'; if (model.subpage === 'upload' && upload === u) render(); else notify('草稿操作已结束，请刷新我的资源或核对待处理操作。');
      }, 'develop', 'primary')));
    if (u.error) add(content, U.summary('预检未完成', u.error, 'bad'), button('重新读取本地文件', async () => {
      const preview = await call('upload_preview', {scanId: u.args.scanId, candidateId: u.args.candidateId});
      if (upload !== u) return; u.preview = preview; u.args.expectedContentHash = preview.contentHash; u.stage = 'preview'; u.plan = null; u.conflict = null; u.draft.bindExisting = u.draft.overwriteDraft = false; u.error = null; render();
    }));
  }
  let selectedOperation = null;
  async function inspect(id) {
    if (!id) { model.enter('operations', scrollY); selectedOperation = null; render(); return; }
    const value = await call('inspect_operation', {operationId: id}); selectedOperation = value;
    model.enter('operations', scrollY); render();
  }
  function operations() {
    const main = $('#main'), op = selectedOperation;
    add(main, U.subpage(op ? '操作记录' : '待处理操作', '返回来源页面', () => { selectedOperation = null; leaveSubpage(); }, `${model.state.profile.displayName || model.state.profile.id} / ${model.state.profile.namespaceId} · 当前上下文`));
    if (!op) {
      const pending = model.state.unfinishedOperations || [];
      add(main, pending.length ? pending.map(x => h('section', {class: 'operation-row'}, h('div', {}, h('h3', {}, x.ref?.name || x.target?.name || M.action(x.action)), badge(M.label(x.status))), button('查看记录', () => inspect(x.id)))) : empty('当前上下文没有待处理的操作。')); return;
    }
    add(main, badge(M.label(op.status)), kv([['操作', M.action(op.action)], ['资源', op.ref?.name || op.target?.name]]),
      h('p', {}, ['result_unknown', 'running'].includes(op.status) ? '结果尚未确认，不应重新发起同一写操作。' : '记录反映已核实的操作结果。'),
      button('刷新记录', () => inspect(op.id)));
    if (['upload', 'submit', 'publish'].includes(op.action) && ['running', 'result_unknown'].includes(op.status)) add(main, form([
      op.action === 'upload' ? field('服务端实际版本（可选）', 'version', '', {placeholder: '草稿已离开编辑态时，填写待核对的确切版本'}) : null,
      h('p', {class: 'muted'}, '只读取服务端状态与内容，不重新发送写入。无法匹配时仍保留未知状态。')
    ], '核对远端结果', async data => {
      selectedOperation = await mutation('reconcile', {operationId: op.id, ...(data.get('version')?.trim() ? {version: data.get('version').trim()} : {})}); render();
    }, {}, 'develop'));
    if ((op.backup || op.configBackup || op.afterHashes) && ['recovery_required', 'failed', 'completed'].includes(op.status)) add(main, actionButton('恢复之前的本地状态…', event => {
      U.confirm(event.currentTarget, '恢复本地状态？', h('p', {}, '仅恢复有证据的受管文件或配置；不撤回远端上传或发布。文件发生额外修改时会拒绝恢复。'), '确认恢复', async () => { selectedOperation = await mutation('recover', {operationId: op.id}); render(); });
    }, 'install'));
    if (op.action?.startsWith('agent') && ['result_unknown', 'running'].includes(op.status)) add(main, h('p', {class: 'muted'}, op.taskHandle ? '可从对应 Agent 的当前任务查询状态。' : '没有有效任务引用，无法安全自动查询。请向服务方核对，不要直接重发。'));
    add(main, raw(op));
  }
  async function start() {
    try { await bridge.initialize(); await load(); notify(''); render(); }
    catch (error) { notify('资源中心连接失败：' + readable(error), true); $('#main').replaceChildren(button('重试连接', start)); }
  }
  start();
})();
