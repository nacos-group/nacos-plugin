# Nacos 3.x 启动报错：Empty identity 的解决说明

## 错误信息

```
errCode: 50002, errMsg: Empty identity, Please set `nacos.core.auth.server.identity.key` and `nacos.core.auth.server.identity.value`
```

## 原因

Nacos 3.x 启用了服务端认证，必须配置 **服务身份标识**，否则 `NacosServerAdminAuthConfig` 校验不通过，导致启动失败。

## 解决步骤

### 1. 找到 Nacos 的配置文件

- **单机/调试**：在 Nacos 工程或运行目录下找到 `application.properties` 或 `application.yml`。
  - 若从 **IDE 调试** 启动（如 D:\code\nacos-3.1.1），通常在：
    - `config/src/main/resources/application.properties`，或
    - 运行目录下的 `conf/application.properties`
  - 若使用 **打包后的 Nacos**，一般在安装目录的 `conf/application.properties`。

### 2. 添加或修改以下两项配置

在 `application.properties` 中增加（若已存在则修改为有效非空值）：

```properties
# 服务身份 key，可自定义，与 value 一起用于集群间认证
nacos.core.auth.server.identity.key=serverIdentity
# 服务身份 value，必须与 key 一起配置，且不要使用默认值暴露在公网
nacos.core.auth.server.identity.value=your-custom-secret-value
```

**注意：**

- `nacos.core.auth.server.identity.key` 和 `nacos.core.auth.server.identity.value` **必须同时配置**，且 value 不要为空。
- 仅本地/调试环境可使用简单值（如上面示例）；**生产环境请使用复杂随机字符串**，并妥善保管。

### 3. 若使用 application.yml

等价配置为：

```yaml
nacos:
  core:
    auth:
      server:
        identity:
          key: serverIdentity
          value: your-custom-secret-value
```

### 4. 保存后重启 Nacos

保存配置文件后重新启动 Nacos（或重新以调试方式启动），上述 50002 错误即可消除。

## 参考

- [Nacos 认证说明](https://nacos.io/docs/latest/manual/admin/auth/)
