/* Copyright 2026 Alibaba Group Holding Ltd. SPDX-License-Identifier: Apache-2.0 */
'use strict';
globalThis.NacosUI = (() => {
  function h(tag, attrs = {}, ...children) {
    const node = document.createElement(tag);
    for (const [key, value] of Object.entries(attrs)) {
      if (value === undefined || value === null || value === false) continue;
      if (key.startsWith('on')) node.addEventListener(key.slice(2), value);
      else if (['disabled', 'checked', 'inert'].includes(key)) node[key] = value;
      else node.setAttribute(key === 'className' ? 'class' : key, String(value));
    }
    for (const value of children.flat(Infinity)) if (value !== null && value !== undefined && value !== false)
      node.append(value instanceof Node ? value : document.createTextNode(String(value)));
    return node;
  }
  const button = (text, action, opts = {}) => h('button', {type: 'button', class: opts.kind || '',
    disabled: opts.disabled, title: opts.reason, 'aria-label': opts.label,
    onclick: event => Promise.resolve().then(() => action(event)).catch(error => notify(error.message, true))}, text);
  const badge = (text, tone = '') => h('span', {class: 'badge ' + tone}, text);
  const raw = value => h('details', {class: 'technical'}, h('summary', {}, '诊断详情'), h('pre', {}, JSON.stringify(value, null, 2)));
  const empty = text => h('div', {class: 'empty'}, text);
  const actions = (...items) => h('div', {class: 'actions action-bar'}, items);
  const summary = (title, body, tone = '') => h('section', {class: 'state-summary ' + tone, role: 'status'},
    h('h3', {}, title), body ? h('p', {}, body) : null);
  const subpage = (title, backLabel, back, subtitle) => h('div', {class: 'subpage-heading'},
    button('‹ ' + backLabel, back, {kind: 'quiet subpage-back'}),
    h('h2', {tabindex: '-1'}, title), subtitle ? h('p', {class: 'muted'}, subtitle) : null);
  function notify(text, error = false) {
    const node = document.querySelector('#notice'); node.textContent = text; node.className = error ? 'error' : '';
  }
  function field(label, name, value = '', attrs = {}) {
    const input = h(attrs.multiline ? 'textarea' : 'input', {name, ...(attrs.multiline ? {} : {value}), ...attrs});
    if (attrs.multiline) input.value = value;
    return h('label', {class: 'field'}, h('span', {}, label), input);
  }
  function select(label, name, options, value) {
    const input = h('select', {name}, options.map(x => h('option', {value: x[0]}, x[1])));
    if (value !== undefined) input.value = value;
    return h('label', {class: 'field'}, h('span', {}, label),
      h('span', {class: 'select-control'}, input, h('span', {class: 'select-chevron', 'aria-hidden': 'true'})));
  }
  const check = (text, name, checked = false) => h('label', {class: 'check'}, h('input', {type: 'checkbox', name, checked}), text);
  let overlay = null;
  function closeOverlay(focus = true) {
    if (!overlay) return;
    const {node, trigger, cleanup} = overlay; overlay = null; cleanup(); node.remove();
    document.querySelector('#workspace').inert = false;
    if (focus && trigger?.isConnected) trigger.focus();
  }
  function menu(trigger, entries) {
    closeOverlay(false);
    const node = h('div', {class: 'popover', role: 'menu', 'aria-label': '资源操作'},
      entries.map(item => button(item.label, () => { closeOverlay(false); return item.run(); },
        {kind: item.danger ? 'menu-item danger' : 'menu-item', disabled: item.disabled, reason: item.reason})));
    for (const [i, b] of [...node.querySelectorAll('button')].entries()) { b.setAttribute('role', 'menuitem'); if (entries[i].disabled && entries[i].reason) b.append(h('small', {class: 'disabled-reason'}, entries[i].reason)); }
    document.body.append(node);
    const position = () => {
      const rect = trigger.getBoundingClientRect(), box = node.getBoundingClientRect();
      node.style.left = Math.max(8, Math.min(innerWidth - box.width - 8, rect.right - box.width)) + 'px';
      node.style.top = Math.max(8, rect.bottom + box.height > innerHeight - 8 ? rect.top - box.height : rect.bottom + 6) + 'px';
    };
    position();
    const outside = e => { if (!node.contains(e.target) && !trigger.contains(e.target)) closeOverlay(); };
    const key = e => {
      const choices = [...node.querySelectorAll('button:not(:disabled)')];
      if (e.key === 'Escape' || e.key === 'Tab') closeOverlay();
      if (['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(e.key)) {
        e.preventDefault(); let index = choices.indexOf(document.activeElement);
        index = e.key === 'Home' ? 0 : e.key === 'End' ? choices.length - 1 : (index + (e.key === 'ArrowDown' ? 1 : -1) + choices.length) % choices.length;
        choices[index]?.focus();
      }
    };
    const resize = position;
    window.addEventListener('resize', resize);
    document.addEventListener('pointerdown', outside); document.addEventListener('keydown', key);
    overlay = {node, trigger, cleanup: () => { window.removeEventListener('resize', resize); document.removeEventListener('pointerdown', outside); document.removeEventListener('keydown', key); }};
    node.querySelector('button:not(:disabled)')?.focus();
  }
  function confirm(trigger, title, content, actionText, action) {
    closeOverlay(false);
    const node = h('dialog', {class: 'confirmation', 'aria-label': title});
    const feedback = h('div', {class: 'error', role: 'status'}); let running = false;
    const cancel = button('取消', () => { if (!running) closeOverlay(); });
    const execute = button(actionText, async () => {
      if (running) return; running = true; cancel.disabled = execute.disabled = true; execute.textContent = '正在执行…';
      try { await action(); closeOverlay(false); document.querySelector('#detail h2, #main h2')?.focus(); }
      catch (error) { feedback.textContent = error.message; running = false; cancel.disabled = false; execute.disabled = true; }
    }, {kind: 'danger'});
    node.append(h('h2', {}, title), content, feedback, h('div', {class: 'actions'}, cancel, execute));
    document.body.append(node); node.addEventListener('cancel', e => { e.preventDefault(); if (!running) closeOverlay(); });
    overlay = {node, trigger, cleanup: () => node.close()}; node.showModal(); cancel.focus();
  }
  return {h, button, badge, raw, empty, notify, field, select, check, menu, confirm, closeOverlay, actions, summary, subpage};
})();
