/* Copyright 2026 Alibaba Group Holding Ltd. SPDX-License-Identifier: Apache-2.0 */
'use strict';
globalThis.NacosSettings = (() => {
  const M = NacosSettingsModel, U = NacosUI, {h, button, badge, field, select, check} = U;
  function create(api) {
    let group = 'connection', editing = false, draft = null, result = null, notice = null;
    let saving = false, generation = 0, errors = {}, failure = null, advanced = false;
    const locale = () => api.locale() || 'zh-CN', t = key => M.t(key, locale());
    const redraw = () => api.changed();
    const reset = () => { generation++; draft = null; editing = false; result = null; notice = null; errors = {}; failure = null; };
    function edit() { draft ||= M.draft(api.state()?.profile); editing = true; notice = null; redraw(); }
    function selectGroup(value, editNow = false) { group = value; if (editNow) { draft ||= M.draft(api.state()?.profile); editing = true; } }
    const help = (text, extra = '') => h('p', {class: 'settings-help ' + extra}, text);
    function pairs(rows) {
      return h('dl', {class: 'settings-facts'}, rows.filter(x => x[1]).map(([key, value]) => [h('dt', {}, key), h('dd', {}, value)]));
    }
    const scopes = p => h('div', {class: 'scope-tags', 'aria-label': t('uses')}, M.scopes.filter(key => p.allowedOperations.includes(key))
      .map(key => h('span', {class: 'badge', title: t(key + 'Help')}, t(key))));
    const problem = error => ({authentication: 'authenticationError', permission: 'permissionError', network: 'networkError'})[error.kind] || 'requestError';
    function advancedSummary(p) {
      return h('details', {class: 'settings-advanced'}, h('summary', {}, t('advanced')),
        help(t('advancedHelp')), pairs([[t('connectionId'), p.id], [t('identityId'), p.identityId], [t('config'), p.codexConfig || t('unset')]]),
        help(t('connectionIdHelp')), help(t('identityIdHelp')));
    }
    async function diagnose() {
      if (result?.status === 'checking' || saving || api.busy()) return;
      const token = ++generation, context = api.state()?.context;
      if (notice === 'saved') notice = null;
      result = {status: 'checking'}; redraw();
      let next;
      try {
        const value = await api.diagnose();
        next = value.clientRead === 'passed'
          ? {status: 'passed', at: value.checkedAt * 1000 || Date.now()}
          : {status: 'failed', message: 'invalidResult', at: Date.now()};
      } catch (error) { next = {status: 'failed', message: problem(error), at: Date.now()}; }
      if (generation !== token || api.state()?.context !== context) return;
      result = next; redraw();
    }
    function connectionSummary(section, p) {
      const separate = M.isSeparate(p);
      section.append(h('h2', {tabindex: '-1'}, p.displayName || t('connection')),
        pairs([[t('namespace'), p.namespaceId], [t('address'), p.clientUrl], [t('auth'), t(p.clientAuth?.type || 'none')]]));
      if (separate) section.append(h('details', {class: 'settings-admin-summary'},
        h('summary', {}, t('adminSeparate')),
        pairs([[t('adminAddress'), p.adminUrl], [t('adminAuth'), t(p.adminAuth?.type || 'none')]])));
      section.append(h('div', {class: 'settings-uses'}, h('h3', {}, t('uses')), scopes(p)));
      const status = result?.status || 'unchecked';
      const checkBox = h('section', {class: 'connection-status', 'aria-live': 'polite', 'aria-busy': status === 'checking'},
        badge(t(status), status === 'passed' ? 'good' : status === 'failed' ? 'bad' : 'warning'));
      if (status === 'passed') checkBox.append(help(t('checkPassed')));
      if (status === 'failed') checkBox.append(h('p', {class: 'error'}, t(result.message)));
      if (result?.at) checkBox.append(h('p', {class: 'settings-help'}, t('checkedAt') + ' · ' + new Date(result.at).toLocaleString(locale())));
      checkBox.append(help(t('checkHelp')), help(t('checkLimits')));
      section.append(checkBox,
        h('div', {class: 'actions settings-actions'}, button(t('edit'), edit, {kind: 'primary', disabled: saving || api.busy()}),
          button(t(result && status !== 'checking' ? 'recheck' : status === 'checking' ? 'checking' : 'check'), diagnose, {disabled: status === 'checking' || saving || api.busy()})),
        advancedSummary(p));
    }
    function directoriesSummary(section, p) {
      section.append(h('h2', {tabindex: '-1'}, t('directories')), help(t('directoriesHelp')));
      for (const [key, hint] of [['scanRoots', 'scanHelp'], ['installRoots', 'installHelpPath']]) section.append(
        h('section', {class: 'settings-directory-section'}, h('h3', {}, t(key)), help(t(hint)),
          p[key].length ? h('ul', {class: 'directory-list'}, p[key].map(path => h('li', {}, path))) : help(t('unset'))));
      section.append(h('div', {class: 'actions'}, button(t('editDirectories'), edit, {kind: 'primary', disabled: saving || api.busy()})));
    }
    function editor(section, p) {
      draft ||= M.draft(p); const d = draft.profile;
      section.append(h('h2', {tabindex: '-1'}, t(group === 'directories' ? 'editDirectories' : 'editing')));
      const form = h('form', {class: 'settings-form', novalidate: true});
      function mark(node, key, hint) {
        const input = node.querySelector('input, select'), error = errors[key];
        const hintId = 'setting-hint-' + key.replaceAll('.', '-');
        if (hint) { node.append(h('small', {id: hintId}, hint)); input.setAttribute('aria-describedby', hintId); }
        if (error) { node.append(h('small', {id: hintId + '-error', class: 'error'}, t(error))); input.setAttribute('aria-invalid', 'true'); input.setAttribute('aria-describedby', [hint && hintId, hintId + '-error'].filter(Boolean).join(' ')); }
        input.addEventListener('input', () => {
          delete errors[key];
          if (!draft.separateAdmin && key === 'clientUrl') delete errors.adminUrl;
          node.querySelector('.error')?.remove(); input.removeAttribute('aria-invalid');
          if (hint) input.setAttribute('aria-describedby', hintId); else input.removeAttribute('aria-describedby');
        });
        return node;
      }
      function bind(label, key, hint, attrs = {}) {
        const node = field(t(label), key, d[key] || '', attrs);
        node.querySelector('input').oninput = e => { d[key] = e.target.value; };
        return mark(node, key, hint && t(hint));
      }
      function authFields(key) {
        const a = d[key], node = h('div', {class: 'settings-auth'});
        const mode = select(t('auth'), key, ['none', 'login', 'token'].map(x => [x, t(x)]), a.type);
        mode.querySelector('select').onchange = e => {
          d[key] = {type: e.target.value};
          for (const name of Object.keys(errors)) if (name.startsWith(key + '.')) delete errors[name];
          redraw();
        };
        node.append(mode);
        for (const name of a.type === 'login' ? ['usernameEnv', 'passwordEnv'] : a.type === 'token' ? ['tokenEnv'] : []) {
          const item = field(t(name), key + '.' + name, a[name] || '', {placeholder: t('envPlaceholder'), spellcheck: 'false', autocomplete: 'off'});
          item.querySelector('input').oninput = e => { a[name] = e.target.value; };
          node.append(mark(item, key + '.' + name));
        }
        if (a.type !== 'none') node.append(help(t('authHelp')));
        return node;
      }
      if (group === 'connection') {
        form.append(bind('name', 'displayName', 'nameHelp', {placeholder: t('optional')}),
          bind('address', 'clientUrl', 'addressHelp', {type: 'url', placeholder: 'https://registry.example.org/nacos'}),
          bind('namespace', 'namespaceId', 'namespaceHelp'), authFields('clientAuth'));
        const separate = check(t('separateAdmin'), 'separateAdmin', draft.separateAdmin);
        separate.querySelector('input').onchange = e => { draft.separateAdmin = e.target.checked; redraw(); };
        form.append(h('div', {class: 'settings-management'}, separate, help(t('adminHelp'))));
        if (draft.separateAdmin) form.append(h('fieldset', {}, h('legend', {}, t('adminAuth')), bind('adminAddress', 'adminUrl', null, {type: 'url'}), authFields('adminAuth')));
        const uses = h('fieldset', {class: 'settings-scopes'}, h('legend', {}, t('uses')), help(t('usesHelp')));
        for (const key of M.scopes) {
          const node = check(t(key) + (key === 'read' ? ' · ' + t('required') : ''), key, d.allowedOperations.includes(key));
          const input = node.querySelector('input'); input.disabled = key === 'read';
          input.onchange = () => { d.allowedOperations = input.checked ? [...new Set([...d.allowedOperations, key])] : d.allowedOperations.filter(x => x !== key); };
          uses.append(h('div', {}, node, help(t(key + 'Help'))));
        }
        form.append(uses);
        const extra = h('details', {class: 'settings-advanced', open: advanced},
          h('summary', {}, t('advanced')), help(t('advancedHelp')),
          bind('connectionId', 'id', 'connectionIdHelp', {readonly: !!p}),
          bind('identityId', 'identityId', 'identityIdHelp'),
          bind('config', 'codexConfig', 'configHelp', {placeholder: '/path/to/.codex/config.toml'}));
        extra.addEventListener('toggle', () => { advanced = extra.open; }); form.append(extra);
      } else {
        form.append(help(t('directoriesHelp')));
        for (const [key, hint] of [['scanRoots', 'scanHelp'], ['installRoots', 'installHelpPath']]) {
          const block = h('section', {class: 'settings-directory-section'}, h('h3', {}, t(key)), help(t(hint)));
          d[key].forEach((path, i) => {
            const node = field(t('directory') + ' ' + (i + 1), key + i, path, {placeholder: t('pathPlaceholder')});
            node.querySelector('input').oninput = e => { d[key][i] = e.target.value; };
            block.append(h('div', {class: 'directory-row'}, mark(node, key + i),
              button(t('removeDirectory'), () => { d[key].splice(i, 1); redraw(); }, {kind: 'quiet', label: t('removeDirectory') + ' ' + (i + 1)})));
          });
          block.append(button(t('addDirectory'), () => { if (d[key].length < 16) { d[key].push(''); redraw(); } }, {disabled: d[key].length >= 16}));
          form.append(block);
        }
      }
      if (failure) form.append(h('p', {class: 'error', role: 'alert'}, t(failure)));
      const submit = h('button', {type: 'submit', class: 'primary', disabled: saving || api.busy()}, t(saving ? 'saving' : 'save'));
      form.append(h('div', {class: 'actions settings-actions'},
        button(t('cancel'), () => { editing = false; notice = 'cancelled'; failure = null; errors = {}; redraw(); }, {disabled: saving || !p}), submit));
      if (saving) for (const input of form.querySelectorAll('input,select,button')) input.disabled = true;
      form.addEventListener('submit', async event => {
        event.preventDefault(); if (saving || api.busy()) return;
        const next = M.serialize(draft); errors = M.validate(next, draft.profile); failure = null;
        if (Object.keys(errors).length) {
          const first = Object.keys(errors)[0]; group = /^(scanRoots|installRoots)/.test(first) ? 'directories' : 'connection';
          if (['id', 'identityId', 'codexConfig'].includes(first)) advanced = true;
          redraw(); document.querySelector('[aria-invalid=true]')?.focus(); return;
        }
        saving = true; redraw();
        try {
          await api.configure(next);
          draft = null; editing = false; notice = 'saved'; result = null; errors = {};
        } catch (error) { failure = problem(error); }
        finally { saving = false; redraw(); }
      });
      section.append(form);
    }
    function render(main) {
      const p = api.state()?.profile;
      main.lang = M.language(locale());
      const nav = h('nav', {class: 'settings-nav', 'aria-label': t('groups')}, ['connection', 'directories'].map(key => {
        const node = button(t(key), () => { group = key; redraw(); }, {kind: 'quiet', disabled: saving});
        node.setAttribute('aria-current', group === key ? 'page' : 'false'); return node;
      }));
      const section = h('section', {class: 'settings-content'});
      if (notice) section.append(h('p', {class: 'settings-notice', role: 'status'}, t(notice)));
      else if (draft && !editing) section.append(help(t('draftKept')));
      if (editing || !p) editor(section, p);
      else if (group === 'connection') connectionSummary(section, p);
      else directoriesSummary(section, p);
      main.append(h('div', {class: 'settings-layout'}, nav, section),
        h('footer', {class: 'settings-version'}, t('version') + ' · ' + api.version));
    }
    return {render, reset, selectGroup, t};
  }
  return {create};
})();
