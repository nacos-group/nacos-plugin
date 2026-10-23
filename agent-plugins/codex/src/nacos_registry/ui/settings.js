/* Copyright 2026 Alibaba Group Holding Ltd. SPDX-License-Identifier: Apache-2.0 */
'use strict';
globalThis.NacosSettings = (() => {
  const M = NacosSettingsModel, U = NacosUI, {h, button, badge, field, select, check} = U;
  function create(api) {
    let group = 'connection', editing = false, draft = null, result = null, notice = null;
    let saving = false, generation = 0, errors = {}, failure = null, advanced = false;
    let secretDraft = {}, incoming = null, dirty = false;
    const locale = () => api.locale() || 'zh-CN', t = key => M.t(key, locale());
    const redraw = () => api.changed();
    const defaults = () => api.state()?.defaults || {};
    const clearSecrets = () => { secretDraft = {}; for (const input of document.querySelectorAll('[data-private-credential]')) input.value = ''; };
    const reset = () => { clearSecrets(); generation++; draft = null; editing = false; result = null; notice = null; errors = {}; failure = null; incoming = null; dirty = false; };
    window.addEventListener('pagehide', clearSecrets);
    function receiveDraft(value, replace = false) {
      if (draft && (dirty || Object.keys(secretDraft).length || saving) && !replace) { incoming = value; redraw(); return; }
      clearSecrets(); draft = M.prefill(api.state()?.profile, value, defaults()); incoming = null;
      group = 'connection'; editing = true; notice = 'prefilled'; failure = null; errors = {}; dirty = true; redraw();
    }
    function edit() { draft ||= M.draft(api.state()?.profile, defaults()); editing = true; notice = null; redraw(); }
    function selectGroup(value, editNow = false) { if (group !== value) clearSecrets(); group = value; if (editNow) { draft ||= M.draft(api.state()?.profile, defaults()); editing = true; } }
    const help = (text, extra = '') => h('p', {class: 'settings-help ' + extra}, text);
    function pairs(rows) {
      return h('dl', {class: 'settings-facts'}, rows.filter(x => x[1]).map(([key, value]) => [h('dt', {}, key), h('dd', {}, value)]));
    }
    const scopes = p => h('div', {class: 'scope-tags', 'aria-label': t('uses')}, M.scopes.filter(key => p.allowedOperations.includes(key))
      .map(key => h('span', {class: 'badge', title: t(key + 'Help')}, t(key))));
    const problem = error => ({authentication: 'authenticationError', permission: 'permissionError', network: 'networkError',
      credential_store: 'credentialError', credential_missing: 'refill', credential_scope: 'scopeError',
      secure_store_unavailable: 'localUnavailable', credential_channel: 'channelError', credential_envelope: 'channelError', credential_crypto: 'encryptionError', credential_session: 'refill', conflict: 'changedContext'})[error.kind] || 'requestError';
    function advancedSummary(p) {
      return h('details', {class: 'settings-advanced'}, h('summary', {}, t('advanced')),
        help(t('advancedHelp')), pairs([[t('connectionId'), p.id], [t('identityId'), p.identityId], [t('config'), p.codexConfig || t('unset')]]),
        help(t('connectionIdHelp')), help(t('identityIdHelp')), help(t('configHelp')));
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
      if (p.clientAuth?.source === 'local') section.append(badge(t(p.clientAuth.credentialRef ? 'credentialSaved' : 'credentialMissing')));
      if (api.state()?.credentialCleanupPending) section.append(help(t('cleanupPending')));
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
      draft ||= M.draft(p, defaults()); const d = draft.profile;
      section.append(h('h2', {tabindex: '-1'}, t(group === 'directories' ? 'editDirectories' : 'editing')));
      const form = h('form', {class: 'settings-form', novalidate: true});
      form.addEventListener('input', () => { dirty = true; });
      form.addEventListener('change', () => { dirty = true; });
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
        node.querySelector('input').oninput = e => {
          const changed = d[key] !== e.target.value;
          d[key] = e.target.value;
          if (changed && ['clientUrl', 'adminUrl', 'id', 'identityId'].includes(key)) {
            clearSecrets();
            // Do not retain a credential reference when its destination changes.
            for (const surface of ['client', 'admin']) if (p && (d[surface + 'Url'] !== p[surface + 'Url'] || d.id !== p.id || d.identityId !== p.identityId)) {
              delete d[surface + 'Auth'].credentialRef;
              delete secretDraft[surface + 'Auth'];
            }
          }
        };
        if (['clientUrl', 'adminUrl', 'id', 'identityId'].includes(key)) node.querySelector('input').onchange = redraw;
        return mark(node, key, hint && t(hint));
      }
      function authFields(key) {
        const a = d[key], node = h('div', {class: 'settings-auth'});
        const available = api.state()?.credentialStorage?.available === true;
        const mode = select(t('auth'), key, ['none', 'login', 'token'].map(x => [x, t(x)]), a.type);
        mode.querySelector('select').onchange = e => {
          clearSecrets(); d[key] = {type: e.target.value, ...(e.target.value !== 'none' && available ? {source: 'local'} : {})};
          for (const name of Object.keys(errors)) if (name.startsWith(key + '.')) delete errors[name];
          redraw();
        };
        node.append(mode);
        if (a.type === 'none') return node;
        const source = select(t('source'), key + '.source', [['local', t('local')], ['environment', t('environment')]], a.source || 'environment');
        source.querySelector('option[value=local]').disabled = !available;
        source.querySelector('select').onchange = e => {
          clearSecrets(); d[key] = {type: a.type, ...(e.target.value === 'local' ? {source: 'local'} : {})}; errors = {}; redraw();
        };
        node.append(source);
        if (!available) node.append(help(t('localUnavailable')));
        if (a.source === 'local') {
          node.append(help(t('localHelp')));
          const edit = secretDraft[key];
          if (edit?.clear) node.append(badge(t('clearStaged')), help(t('clearHelp')));
          else if (a.credentialRef && !edit) node.append(badge(t('credentialSaved')));
          else {
            for (const name of a.type === 'login' ? ['username', 'password'] : ['token']) {
              const item = field(t(name === 'token' ? 'secretToken' : name), key + '.' + name, '',
                {type: name === 'username' ? 'text' : 'password', autocomplete: 'off', spellcheck: 'false',
                  'data-private-credential': 'true', maxlength: name === 'username' ? 256 : name === 'token' ? 8192 : 4096});
              const input = item.querySelector('input'); input.value = edit?.[name] || '';
              input.oninput = e => { (secretDraft[key] ||= {})[name] = e.target.value; };
              node.append(mark(item, key + '.' + name));
            }
          }
          if (a.credentialRef || edit?.clear) node.append(h('div', {class: 'actions'},
            button(t('replaceCredential'), () => { clearSecrets(); secretDraft[key] = {}; redraw(); }),
            a.credentialRef && !edit?.clear ? button(t('clearCredential'), event => U.confirm(event.currentTarget,
              t('clearConfirm'), h('p', {}, t('clearHelp')), t('confirmClear'), () => {
                clearSecrets(); secretDraft[key] = {clear: true}; redraw();
              })) : null));
          return node;
        }
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
        separate.querySelector('input').onchange = e => {
          clearSecrets(); draft.separateAdmin = e.target.checked;
          if (!draft.separateAdmin && d.clientAuth.source === 'local' && M.isSeparate(d)) delete d.clientAuth.credentialRef;
          redraw();
        };
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
        const configField = bind('config', 'codexConfig', 'configHelp', {placeholder: defaults().codexConfig || '/path/to/.codex/config.toml'});
        const defaultConfig = button(t('useDefaultConfig'), () => { d.codexConfig = defaults().codexConfig; dirty = true; redraw(); },
          {disabled: !defaults().codexConfig || d.codexConfig === defaults().codexConfig});
        configField.querySelector('input').addEventListener('input', () => {
          defaultConfig.disabled = !defaults().codexConfig || d.codexConfig.trim() === defaults().codexConfig;
        });
        const extra = h('details', {class: 'settings-advanced', open: advanced},
          h('summary', {}, t('advanced')), help(t('advancedHelp')),
          bind('connectionId', 'id', 'connectionIdHelp', {readonly: !!p}),
          bind('identityId', 'identityId', 'identityIdHelp'),
          configField, defaultConfig);
        extra.addEventListener('toggle', () => { advanced = extra.open; }); form.append(extra);
      } else {
        form.append(help(t('directoriesHelp')), help(t('defaultDirectoryHelp')));
        for (const [key, hint] of [['scanRoots', 'scanHelp'], ['installRoots', 'installHelpPath']]) {
          const block = h('section', {class: 'settings-directory-section'}, h('h3', {}, t(key)), help(t(hint)));
          const defaultsDisabled = () => d[key].filter(x => x.trim()).length >= 16 || !(defaults()[key] || []).some(x => !d[key].some(y => y.trim() === x));
          const defaultRoots = button(t('addDefaults'), () => { M.addDefaultRoots(draft, key, defaults()); dirty = true; redraw(); }, {disabled: defaultsDisabled()});
          d[key].forEach((path, i) => {
            const node = field(t('directory') + ' ' + (i + 1), key + i, path, {placeholder: t('pathPlaceholder')});
            node.querySelector('input').oninput = e => { d[key][i] = e.target.value; defaultRoots.disabled = defaultsDisabled(); };
            block.append(h('div', {class: 'directory-row'}, mark(node, key + i),
              button(t('removeDirectory'), () => { dirty = true; d[key].splice(i, 1); redraw(); }, {kind: 'quiet', label: t('removeDirectory') + ' ' + (i + 1)})));
          });
          block.append(h('div', {class: 'actions'},
            button(t('addDirectory'), () => { if (d[key].length < 16) { dirty = true; d[key].push(''); redraw(); } }, {disabled: d[key].length >= 16}),
            defaultRoots));
          form.append(block);
        }
      }
      if (failure) form.append(h('p', {class: 'error', role: 'alert'}, t(failure)),
        button(t('reloadSaved'), async () => {
          clearSecrets(); saving = true; redraw();
          try { await api.reload(); reset(); }
          catch (error) { failure = problem(error); }
          finally { saving = false; redraw(); }
        }, {disabled: saving}));
      const submit = h('button', {type: 'submit', class: 'primary', disabled: saving || api.busy()}, t(saving ? 'saving' : 'save'));
      form.append(h('div', {class: 'actions settings-actions'},
        button(t('cancel'), () => { clearSecrets(); editing = false; notice = 'cancelled'; failure = null; errors = {}; redraw(); }, {disabled: saving || !p}), submit));
      if (saving) for (const input of form.querySelectorAll('input,select,button')) input.disabled = true;
      form.addEventListener('submit', async event => {
        event.preventDefault(); if (saving || api.busy()) return;
        const next = M.serialize(draft), changes = M.credentialChanges(draft, secretDraft);
        errors = M.validate(next, draft.profile, changes); failure = null;
        if (Object.keys(errors).length) {
          const first = Object.keys(errors)[0]; group = /^(scanRoots|installRoots)/.test(first) ? 'directories' : 'connection';
          if (['id', 'identityId', 'codexConfig'].includes(first)) advanced = true;
          redraw(); document.querySelector('[aria-invalid=true]')?.focus(); return;
        }
        saving = true; redraw();
        try {
          const saved = Object.keys(changes).length ? await api.configureCredentials(next, changes) : await api.configure(next);
          draft = null; dirty = false; editing = false; notice = saved?.credentialCleanupPending ? 'cleanupPending' : 'saved'; result = null; errors = {};
        } catch (error) { failure = problem(error); }
        finally { clearSecrets(); saving = false; redraw(); }
      });
      section.append(form);
    }
    function render(main) {
      const p = api.state()?.profile;
      main.lang = M.language(locale());
      const nav = h('nav', {class: 'settings-nav', 'aria-label': t('groups')}, ['connection', 'directories'].map(key => {
        const node = button(t(key), () => { if (group !== key) clearSecrets(); group = key; redraw(); }, {kind: 'quiet', disabled: saving});
        node.setAttribute('aria-current', group === key ? 'page' : 'false'); return node;
      }));
      const section = h('section', {class: 'settings-content'});
      if (incoming) section.append(h('section', {class: 'state-summary'}, h('p', {}, t('incomingDraft')),
        h('div', {class: 'actions'}, button(t('useDraft'), () => receiveDraft(incoming, true), {disabled: saving}),
          button(t('keepDraft'), () => { incoming = null; redraw(); }))));
      if (notice) section.append(h('p', {class: 'settings-notice', role: 'status'}, t(notice)));
      else if (draft && dirty && !editing) section.append(help(t('draftKept')));
      if (editing || !p) {
        for (const warning of defaults().warnings || []) section.append(help(t(warning)));
        editor(section, p);
      }
      else if (group === 'connection') connectionSummary(section, p);
      else directoriesSummary(section, p);
      main.append(h('div', {class: 'settings-layout'}, nav, section),
        h('footer', {class: 'settings-version'}, t('version') + ' · ' + api.version));
    }
    return {render, reset, selectGroup, t, receiveDraft, leave: clearSecrets};
  }
  return {create};
})();
