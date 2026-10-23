/* Copyright 2026 Alibaba Group Holding Ltd. SPDX-License-Identifier: Apache-2.0 */
'use strict';
globalThis.NacosSettingsModel = (() => {
  const messages = {
    settings: ['设置', 'Settings'],
    back: ['返回资源中心', 'Back to resource center'],
    unconfigured: ['尚未配置资源中心', 'No connection configured'],
    connection: ['连接与认证', 'Connection & authentication'],
    directories: ['技能目录', 'Skill directories'],
    groups: ['设置分组', 'Settings sections'],
    edit: ['编辑连接', 'Edit connection'],
    editDirectories: ['编辑目录', 'Edit directories'],
    editing: ['编辑连接', 'Edit connection'],
    name: ['显示名称', 'Display name'],
    nameHelp: ['用于在页面上辨认这条连接，例如“团队资源库”。', 'A name such as “Team registry” helps identify this connection.'],
    optional: ['可选', 'Optional'],
    address: ['Nacos 地址', 'Nacos URL'],
    addressHelp: ['填写提供资源 API 的地址，包含部署路径。请勿填写 Console 页面地址。', 'Use the resource API base URL, including its deployment path. Do not use a Console page URL.'],
    namespace: ['命名空间', 'Namespace'],
    namespaceHelp: ['填写资源所在的命名空间 ID。', 'The namespace ID containing your resources.'],
    auth: ['认证方式', 'Authentication'],
    none: ['无需认证', 'No authentication'],
    login: ['Nacos 用户名与密码', 'Nacos username & password'],
    token: ['访问令牌', 'Access token'],
    source: ['凭据提供方式', 'Credential source'],
    local: ['在页面填写', 'Enter in this page'],
    environment: ['使用环境变量', 'Use environment variables'],
    username: ['用户名', 'Username'],
    password: ['密码', 'Password'],
    secretToken: ['访问令牌', 'Access token'],
    localHelp: ['凭据在页面加密后保存到 macOS 钥匙串，明文不写入对话或普通配置。系统可能询问钥匙串访问权限。', 'Credentials are encrypted in this page and saved to macOS Keychain. Plaintext is not included in chat or ordinary configuration. macOS may ask for Keychain access.'],
    localUnavailable: ['当前系统尚不支持页面凭据存储，请选择环境变量或稍后继续。', 'Page credential storage is unavailable on this system. Use environment variables or continue later.'],
    credentialSaved: ['已保存到本机钥匙串', 'Saved in local Keychain'],
    credentialMissing: ['尚未保存凭据', 'Credentials not saved'],
    replaceCredential: ['更换凭据', 'Replace credentials'],
    clearCredential: ['清除已保存凭据…', 'Clear saved credentials…'],
    clearConfirm: ['清除这条连接的凭据？', 'Clear credentials for this connection?'],
    clearHelp: ['点击“保存配置”后生效。随后需要重新填写凭据才能访问 Nacos。', 'Takes effect when you save configuration. You will need to enter credentials again to access Nacos.'],
    clearStaged: ['保存配置后清除凭据', 'Clear credentials on save'],
    confirmClear: ['确认清除', 'Confirm clear'],
    refill: ['请重新填写凭据。非敏感输入已保留。', 'Enter credentials again. Nonsecret fields have been kept.'],
    credentialError: ['无法访问系统钥匙串，请检查钥匙串权限后重试。', 'Cannot access system Keychain. Check Keychain permissions and retry.'],
    channelError: ['未能确认保存结果。请重新读取已保存设置核对；若刚升级插件，请关闭旧页面并重新打开。不要在聊天中发送凭据。', 'Save could not be confirmed. Reload saved settings to check. If you just updated the plugin, close the old page and reopen it. Do not send credentials in chat.'],
    encryptionError: ['页面无法安全加密凭据，本次未提交。请更新插件并重新打开资源中心，再填写凭据。', 'The page could not encrypt credentials safely; nothing was submitted. Update the plugin, reopen the resource center and enter credentials again.'],
    reloadSaved: ['放弃草稿并重新读取', 'Discard draft and reload'],
    scopeError: ['地址或身份已改变，请为新目标重新填写凭据。', 'The URL or identity changed. Enter credentials again for the new destination.'],
    cleanupPending: ['配置已保存，但旧凭据尚未清除。请检查钥匙串权限，再编辑并保存以重试清理。', 'Configuration saved, but old credentials have not been cleared. Check Keychain permissions, then edit and save to retry cleanup.'],
    prefilled: ['已填入对话提供的连接信息，请核对并填写凭据后保存。', 'Connection details from the conversation are ready. Review them, enter credentials and save.'],
    incomingDraft: ['对话提供了新的连接草稿。当前编辑尚未保存。', 'The conversation supplied new connection details. Your current edits are not saved.'],
    useDraft: ['使用新草稿', 'Use new draft'],
    keepDraft: ['继续当前编辑', 'Keep current edits'],
    changedContext: ['连接已被其他页面修改。请重新读取已保存设置后核对。', 'Another page changed the connection. Reload saved settings to review.'],
    usernameEnv: ['用户名环境变量名', 'Username environment variable'],
    passwordEnv: ['密码环境变量名', 'Password environment variable'],
    tokenEnv: ['令牌环境变量名', 'Token environment variable'],
    envPlaceholder: ['只填写变量名', 'Variable name only'],
    authHelp: ['插件从本机环境变量读取凭据。这里填写变量名，不填写密码或令牌。', 'The plugin reads credentials from local environment variables. Enter variable names, not passwords or tokens.'],
    separateAdmin: ['为上传和发布单独配置管理连接', 'Use a separate management connection for upload and publication'],
    adminHelp: ['通常与上方连接相同。仅在管理 API 地址或认证不同的情况下单独设置。', 'Usually the same as the connection above. Configure separately only when the management API URL or authentication differs.'],
    adminAddress: ['管理 API 地址', 'Management API URL'],
    adminAuth: ['管理认证', 'Management authentication'],
    adminSeparate: ['管理连接使用独立设置', 'Management connection configured separately'],
    uses: ['允许的操作', 'Allowed operations'],
    usesHelp: ['这些选项限制插件在本机可以执行的操作，实际权限仍由 Nacos 决定。', 'These options limit what the plugin may do locally. Nacos still determines server permissions.'],
    read: ['发现与读取', 'Discover & read'],
    install: ['安装与更新技能', 'Install & update skills'],
    develop: ['上传与管理技能', 'Upload & manage skills'],
    publish: ['提交与发布', 'Submit & publish'],
    call: ['接入与调用服务', 'Connect & call services'],
    required: ['必需', 'Required'],
    readHelp: ['搜索和读取可见资源。', 'Search and read visible resources.'],
    installHelp: ['安装、更新和卸载本地技能。', 'Install, update and remove local skills.'],
    developHelp: ['上传草稿，管理自己拥有的技能。', 'Upload drafts and manage your own skills.'],
    publishHelp: ['提交审核或发布选定版本。', 'Submit for review or publish a selected version.'],
    callHelp: ['接入 MCP 或 Agent，并执行授权调用。', 'Connect MCP or Agent services and make authorized calls.'],
    advanced: ['高级', 'Advanced'],
    connectionId: ['本地连接标识', 'Local connection ID'],
    connectionIdHelp: ['新连接默认使用本机 hostname，关联本地安装、接入和操作记录；不是 Nacos 服务端 ID。已有连接保持不变。', 'New connections default to this computer’s hostname. Links local records, not a Nacos server ID. Existing IDs stay unchanged.'],
    identityId: ['本地身份标签', 'Local identity label'],
    identityIdHelp: ['新连接默认使用当前系统用户名，仅作本地标签，不代表 Nacos 登录账号或权限。切换 Nacos 账号时请使用不同标签。', 'New connections default to the OS username as a local label, not a Nacos account or permission. Use a different label when switching Nacos accounts.'],
    config: ['Codex 配置文件', 'Codex configuration file'],
    configHelp: ['接入 MCP 工具服务时写入的 Codex 用户配置文件，默认位于 CODEX_HOME（通常是 ~/.codex）。保存此路径不会修改文件，接入计划确认后才写入受管配置。', 'Codex user configuration for MCP tool services, under CODEX_HOME (normally ~/.codex). Saving this path does not modify the file; a confirmed connection plan writes managed entries.'],
    advancedHelp: ['本地记录与应用适配信息，日常连接无需修改。', 'Local record identifiers and app configuration, usually left unchanged.'],
    scanRoots: ['扫描目录', 'Scan directories'],
    scanHelp: ['从这些目录中盘点可跟踪或上传的技能。保存目录不会自动扫描或上传。', 'Find skills to track or upload in these directories. Saving does not scan or upload files.'],
    installRoots: ['技能安装目录', 'Skill installation directories'],
    installHelpPath: ['安装技能时可选择的目标目录。', 'Available destinations when installing a skill.'],
    addDefaults: ['添加默认目录', 'Add default directories'],
    useDefaultConfig: ['使用默认配置文件', 'Use default configuration file'],
    defaultDirectoryHelp: ['默认安装到 ~/.agents/skills；扫描建议只包含已存在的个人技能目录及 Codex 历史技能目录。保存不会扫描、上传或创建目录。', 'Install defaults to ~/.agents/skills. Scan suggestions include existing personal and legacy Codex skill directories only. Saving does not scan, upload or create directories.'],
    defaultSkillsUnavailable: ['个人技能默认目录不可用，请指定其他目录。符号链接及系统缓存目录不作为受管目标。', 'The personal skill directory is unavailable. Choose another directory; symlinks and system caches cannot be managed.'],
    defaultConfigUnavailable: ['未能确定安全的 Codex 配置路径，请核对 CODEX_HOME 或手动填写。', 'A safe Codex configuration path could not be determined. Check CODEX_HOME or enter it manually.'],
    defaultScanUnavailable: ['部分 Codex 历史技能目录无法作为扫描目录，请按需指定其他目录。', 'Some legacy Codex skill directories cannot be scanned. Specify another directory if needed.'],
    defaultIdentityUnavailable: ['未能读取完整的本机标签，已使用通用初始值；可在高级设置修改。', 'Local labels could not be fully detected. Generic initial values are editable in Advanced settings.'],
    directory: ['目录', 'Directory'],
    pathPlaceholder: ['完整目录路径', 'Full directory path'],
    addDirectory: ['添加目录', 'Add directory'],
    removeDirectory: ['移除目录', 'Remove directory'],
    unset: ['未设置', 'Not configured'],
    directoriesHelp: ['这里只配置目录。盘点和上传请从“我的资源 → 本地技能”进入。', 'Configure directories here. To scan or upload, open “My resources → Local skills”.'],
    saved: ['已保存，尚未检查连接。', 'Saved. Connection not checked yet.'],
    cancelled: ['已取消编辑。非敏感输入已暂存；秘密输入已清空。', 'Editing canceled. Nonsecret fields are kept; secret inputs have been cleared.'],
    draftKept: ['有未保存的输入，点击编辑可继续。', 'An unsaved draft is available. Select Edit to resume.'],
    save: ['保存配置', 'Save configuration'],
    saving: ['正在保存…', 'Saving…'],
    cancel: ['取消', 'Cancel'],
    unchecked: ['尚未检查连接', 'Connection not checked'],
    checking: ['正在检查连接…', 'Checking connection…'],
    passed: ['资源读取正常', 'Resource access verified'],
    failed: ['连接检查失败', 'Connection check failed'],
    check: ['检查连接', 'Check connection'],
    recheck: ['重新检查', 'Check again'],
    checkHelp: ['使用当前认证读取一次资源列表，检查地址、网络和读取权限。', 'Read the resource list with the current authentication to check the URL, network and read access.'],
    checkLimits: ['此检查不验证上传、发布或下游 MCP / Agent 权限。', 'This does not verify upload, publication or downstream MCP / Agent permissions.'],
    checkPassed: ['Nacos 已成功响应资源读取请求。', 'Nacos successfully responded to the resource read request.'],
    checkedAt: ['检查时间', 'Checked at'],
    invalidResult: ['未取得可核实的读取结果，请重新检查。', 'No verifiable read result was returned. Please check again.'],
    authenticationError: ['认证失败，请核对已保存的凭据或所引用的环境变量。', 'Authentication failed. Check saved credentials or the referenced environment variables.'],
    networkError: ['无法连接 Nacos，请检查地址、网络及服务是否启动。', 'Cannot reach Nacos. Check the URL, network and whether the service is running.'],
    permissionError: ['当前身份无法读取资源，请检查 Nacos 权限。', 'This identity cannot read resources. Check Nacos permissions.'],
    requestError: ['请求失败，非敏感输入已保留，秘密输入已清空。请核对已保存设置后重试。', 'The request failed. Nonsecret fields are preserved; secret inputs are cleared. Review saved settings before retrying.'],
    details: ['错误详情', 'Error details'],
    version: ['插件版本', 'Plugin version'],
    invalidUrl: ['请输入有效的 HTTP(S) API 地址，不要包含用户名或密码。', 'Enter a valid HTTP(S) API URL without a username or password.'],
    invalidEnv: ['变量名须以大写字母开头，仅包含大写字母、数字或下划线。', 'Use an environment variable name starting with an uppercase letter, containing only uppercase letters, digits or underscores.'],
    missing: ['请填写此项。', 'This field is required.'],
    invalidPath: ['请填写完整路径。', 'Enter an absolute path.'],
  };
  const language = locale => /^en(?:[-_]|$)/i.test(locale || '') ? 'en' : 'zh-CN';
  const t = (key, locale) => messages[key]?.[language(locale) === 'en' ? 1 : 0] ?? key;
  const scopes = ['read', 'install', 'develop', 'publish', 'call'];
  function sameAuth(a, b) {
    a ||= {type: 'none'}; b ||= {type: 'none'};
    return ['type', 'source', 'credentialRef', 'usernameEnv', 'passwordEnv', 'tokenEnv'].every(key => a[key] === b[key]);
  }
  function isSeparate(p) { return p.adminUrl !== p.clientUrl || !sameAuth(p.clientAuth, p.adminAuth); }
  function draft(profile, defaults = {}) {
    const p = structuredClone(profile || {id: defaults.id || 'primary', displayName: '', identityId: defaults.identityId || 'current-user', namespaceId: 'public',
      clientUrl: '', adminUrl: '', clientAuth: {type: 'none'}, adminAuth: {type: 'none'}, allowedOperations: ['read'],
      scanRoots: defaults.scanRoots || [], installRoots: defaults.installRoots || [], codexConfig: defaults.codexConfig || ''});
    return {profile: p, separateAdmin: !!profile && isSeparate(p)};
  }
  function serialize(d) {
    const p = structuredClone(d.profile);
    for (const key of ['displayName', 'clientUrl', 'adminUrl', 'namespaceId', 'id', 'identityId', 'codexConfig'])
      if (typeof p[key] === 'string') p[key] = p[key].trim();
    if (!d.separateAdmin) { p.adminUrl = p.clientUrl; p.adminAuth = structuredClone(p.clientAuth); }
    for (const key of ['scanRoots', 'installRoots']) p[key] = p[key].map(x => x.trim()).filter(Boolean);
    if (!p.codexConfig) delete p.codexConfig;
    return p;
  }
  function validate(p, original = p, changes = {}) {
    const errors = {};
    for (const key of ['id', 'identityId', 'namespaceId']) if (!p[key]) errors[key] = 'missing';
    for (const key of ['clientUrl', 'adminUrl']) {
      try {
        const url = new URL(p[key]);
        if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password || url.search || url.hash) throw new Error();
      } catch { errors[key] = 'invalidUrl'; }
    }
    for (const key of ['clientAuth', 'adminAuth']) {
      const auth = p[key];
      if (auth.source === 'local') {
        const change = changes[key.replace('Auth', '')];
        if (change?.clear) continue;
        if (!change && auth.credentialRef) continue;
        for (const name of auth.type === 'login' ? ['username', 'password'] : ['token'])
          if (!change?.[name]) errors[key + '.' + name] = 'missing';
        continue;
      }
      for (const field of auth.type === 'login' ? ['usernameEnv', 'passwordEnv'] : auth.type === 'token' ? ['tokenEnv'] : [])
        if (!/^[A-Z][A-Z0-9_]{0,127}$/.test(auth[field] || '')) errors[key + '.' + field] = 'invalidEnv';
    }
    for (const key of ['scanRoots', 'installRoots'])
      original[key].forEach((path, i) => { if (path.trim() && !/^(\/|[A-Za-z]:[\\/])/.test(path.trim())) errors[key + i] = 'invalidPath'; });
    if (p.codexConfig && !/^(\/|[A-Za-z]:[\\/])/.test(p.codexConfig)) errors.codexConfig = 'invalidPath';
    return errors;
  }
  function prefill(profile, patch, defaults = {}) {
    const d = draft(profile, defaults), keys = ['displayName', 'namespaceId', 'clientUrl', 'adminUrl', 'clientAuth', 'adminAuth', 'allowedOperations', 'scanRoots', 'installRoots', 'codexConfig'];
    for (const key of keys) if (Object.hasOwn(patch, key)) d.profile[key] = structuredClone(patch[key]);
    for (const surface of ['client', 'admin']) if (profile && d.profile[surface + 'Url'] !== profile[surface + 'Url'])
      delete d.profile[surface + 'Auth'].credentialRef;
    if (patch.adminUrl !== undefined || patch.adminAuth !== undefined) d.separateAdmin = true;
    return d;
  }
  function addDefaultRoots(d, key, defaults = {}) {
    const current = d.profile[key].map(x => x.trim()).filter(Boolean);
    d.profile[key] = [...new Set([...current, ...(defaults[key] || [])])].slice(0, 16);
  }
  function credentialChanges(d, edits) {
    const changes = {};
    for (const surface of ['client', 'admin']) {
      const key = (surface === 'admin' && !d.separateAdmin ? 'client' : surface) + 'Auth';
      if (d.profile[key].source === 'local' && edits[key]) changes[surface] = structuredClone(edits[key]);
    }
    return changes;
  }
  return {language, t, scopes, draft, serialize, validate, isSeparate, prefill, addDefaultRoots, credentialChanges};
})();
