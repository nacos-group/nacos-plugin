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
    connectionIdHelp: ['插件用它关联安装、接入和操作记录，不是 Nacos 服务端 ID。已有连接保持不变。', 'Links local installations, connections and operations. This is not a Nacos server ID. Keep it unchanged for an existing connection.'],
    identityId: ['本地身份标签', 'Local identity label'],
    identityIdHelp: ['用于隔离不同账号的本地记录，不是登录用户名，也不赋予权限。切换 Nacos 账号时请使用不同标签。', 'Separates local records for different accounts. This is not a login username and grants no permissions. Use a different label when switching Nacos accounts.'],
    config: ['Codex 配置文件', 'Codex configuration file'],
    configHelp: ['接入 MCP 时使用的 config.toml 完整路径。', 'Full path to the config.toml file used for MCP connections.'],
    advancedHelp: ['本地记录与应用适配信息，日常连接无需修改。', 'Local record identifiers and app configuration, usually left unchanged.'],
    scanRoots: ['扫描目录', 'Scan directories'],
    scanHelp: ['从这些目录中盘点可跟踪或上传的技能。保存目录不会自动扫描或上传。', 'Find skills to track or upload in these directories. Saving does not scan or upload files.'],
    installRoots: ['技能安装目录', 'Skill installation directories'],
    installHelpPath: ['安装技能时可选择的目标目录。', 'Available destinations when installing a skill.'],
    directory: ['目录', 'Directory'],
    pathPlaceholder: ['完整目录路径', 'Full directory path'],
    addDirectory: ['添加目录', 'Add directory'],
    removeDirectory: ['移除目录', 'Remove directory'],
    unset: ['未设置', 'Not configured'],
    directoriesHelp: ['这里只配置目录。盘点和上传请从“我的资源 → 本地技能”进入。', 'Configure directories here. To scan or upload, open “My resources → Local skills”.'],
    saved: ['已保存，尚未检查连接。', 'Saved. Connection not checked yet.'],
    cancelled: ['已取消编辑。输入已暂存，可重新编辑继续。', 'Editing canceled. Your draft is kept for when you resume.'],
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
    authenticationError: ['认证失败，请核对所引用的用户名、密码或令牌环境变量。', 'Authentication failed. Check the referenced username, password or token variables.'],
    networkError: ['无法连接 Nacos，请检查地址、网络及服务是否启动。', 'Cannot reach Nacos. Check the URL, network and whether the service is running.'],
    permissionError: ['当前身份无法读取资源，请检查 Nacos 权限。', 'This identity cannot read resources. Check Nacos permissions.'],
    requestError: ['请求失败，输入已保留。请检查配置后重试。', 'The request failed. Your input is preserved. Check the configuration and retry.'],
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
    return ['type', 'usernameEnv', 'passwordEnv', 'tokenEnv'].every(key => a[key] === b[key]);
  }
  function isSeparate(p) { return p.adminUrl !== p.clientUrl || !sameAuth(p.clientAuth, p.adminAuth); }
  function draft(profile) {
    const p = structuredClone(profile || {id: 'primary', displayName: '', identityId: 'current-user', namespaceId: 'public',
      clientUrl: '', adminUrl: '', clientAuth: {type: 'none'}, adminAuth: {type: 'none'}, allowedOperations: ['read'],
      scanRoots: [], installRoots: [], codexConfig: ''});
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
  function validate(p, original = p) {
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
      for (const field of auth.type === 'login' ? ['usernameEnv', 'passwordEnv'] : auth.type === 'token' ? ['tokenEnv'] : [])
        if (!/^[A-Z][A-Z0-9_]{0,127}$/.test(auth[field] || '')) errors[key + '.' + field] = 'invalidEnv';
    }
    for (const key of ['scanRoots', 'installRoots'])
      original[key].forEach((path, i) => { if (path.trim() && !/^(\/|[A-Za-z]:[\\/])/.test(path.trim())) errors[key + i] = 'invalidPath'; });
    if (p.codexConfig && !/^(\/|[A-Za-z]:[\\/])/.test(p.codexConfig)) errors.codexConfig = 'invalidPath';
    return errors;
  }
  return {language, t, scopes, draft, serialize, validate, isSeparate};
})();
