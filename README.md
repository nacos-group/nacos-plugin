# nacos-plugin
Nacos 生态插件集合，包含安装到 Nacos Server 的扩展，以及安装到 coding agent / personal agent 的接入插件。

## 按安装位置选择

| 安装位置 | 插件 | 安装、开发与兼容入口 |
| --- | --- | --- |
| Nacos Server | 数据库、加密、自定义环境、配置变更、追踪及 AI 导入插件 | 本页下方的服务端插件安装、版本映射和 Maven 开发指南。 |
| Agent 应用 | Nacos AI Registry：发现、管理和使用 agentic 资源 | [插件入口](agent-plugins/README.md)、[通用规范](agent-plugins/specs/README.md)、[Codex 设计](agent-plugins/codex/README.md)。 |

两类插件分别构建与发布。Agent 插件不安装到 Nacos Server，也不加入根 Maven 构建；
其版本、运行依赖以及与 Nacos 和 Agent 应用的兼容关系由组件独立维护。

![](https://tva1.sinaimg.cn/large/008i3skNly1gxmnilyukqj30qp0fgglx.jpg)

## 一、服务端插件版本映射关系

以下版本映射仅适用于服务端插件：

| 插件 Tag 版本 | 支持的 Nacos 版本        |
|-----------|---------------------|
| 2.2.x     | Nacos 2.2.x         |
| 2.3.x     | Nacos 2.3.x         |
| 2.4.x     | Nacos 2.4.x         |
| 2.5.x     | Nacos 2.5.x         |
| 3.1.x     | Nacos 3.0.x ~ 3.1.x |

**注意**：请选择与您使用的 Nacos 版本相匹配的插件版本进行安装。

> 3.1.x 对kingbase的数据库插件做了较大的改动，用户若从2.x版本升级到3.x版本时，请先阅读[kingbase插件的README](nacos-datasource-plugin-ext/nacos-kingbase-datasource-plugin-ext/README.md)，并在测试环境中确认无误后再进行生产环境的升级。

## 二、服务端插件安装说明

### 2.1 编译插件

在项目根目录下执行以下命令进行编译：

```bash
mvn clean package
```

### 2.2 部署插件

编译完成后，将对应插件目录下的 `target` 文件夹中的 JAR 包复制到 Nacos 的 `plugins` 目录下：

```bash
# 示例：复制插件到 Nacos 插件目录
cp <插件模块>/target/<插件名称>.jar <NACOS_HOME>/plugins/
```

**说明**：
- `<插件模块>`: 对应的插件子模块目录
- `<插件名称>`: 具体的插件 JAR 包名称
- `<NACOS_HOME>`: 您的 Nacos 安装目录

### 2.3 配置插件

根据具体插件的使用说明，在 Nacos 的配置文件（如 `application.properties`）中进行相应配置。

## 三、服务端插件列表

### 3.1 数据源扩展插件 (nacos-datasource-plugin-ext)

提供多种数据库适配插件，支持 Nacos 使用不同的数据库作为后端存储。

`nacos-postgresql-datasource-plugin-ext`已由主仓库维护，查看[nacos-postgresql-datasource-plugin-ext](https://github.com/alibaba/nacos/tree/develop/plugin-default-impl/nacos-default-datasource-plugin/nacos-datasource-plugin-postgresql)

**子插件列表**：
- **nacos-datasource-plugin-ext-base**: 数据库插件基础抽象模块
- **nacos-dm-datasource-plugin-ext**: 达梦数据库适配插件
- **nacos-kingbase-datasource-plugin-ext**: 人大金仓数据库适配插件
- **nacos-mssql-datasource-plugin-ext**: SQL Server 数据库适配插件
- **nacos-oceanbase-datasource-plugin-ext**: OceanBase 数据库适配插件
- **nacos-opengauss-datasource-plugin-ext**: openGauss 数据库适配插件
- **nacos-oracle-datasource-plugin-ext**: Oracle 数据库适配插件
- **nacos-xuguDB-datasource-plugin-ext**: 虚谷数据库适配插件
- **nacos-yashan-datasource-plugin-ext**: 崖山数据库适配插件

详细说明请参考：[nacos-datasource-plugin-ext/README.md](nacos-datasource-plugin-ext/README.md)

### 3.2 加密插件 (nacos-encryption-plugin-ext)

提供数据加密能力扩展插件。

**子插件列表**：
- **nacos-aes-encryption-plugin**: AES 加密算法插件

### 3.3 自定义环境插件 (nacos-custom-environment-plugin-ext)

提供自定义环境处理能力。

**子插件列表**：
- **nacos-db-password-encryption-plugin**: 数据库密码加密插件

### 3.4 配置变更插件 (nacos-config-change-plugin-ext)

提供配置变更时的扩展处理能力。

**子插件列表**：
- **nacos-whitelist-config-change-plugin**: 白名单配置变更插件
- **nacos-fileformat-config-change-plugin**: 文件格式配置变更插件
- **nacos-webhook-config-change-plugin**: Webhook 配置变更通知插件

### 3.5 追踪日志插件 (nacos-trace-plugin-ext)

提供链路追踪和日志记录能力。

**子插件列表**：
- **nacos-trace-logging-plugin**: Nacos 日志命名追踪插件

### 3.6 AI 导入插件 (nacos-ai-importer-plugin-ext)

提供 AI 资源导入适配，参见 [AI 导入插件说明](nacos-ai-importer-plugin-ext/README.md)。

## 四、服务端插件开发指南

### 4.1 项目结构

```
nacos-plugin/
├── agent-plugins/                       # 按 Agent 应用组织的插件
│   ├── specs/                          # 通用规范
│   └── codex/                          # Codex 适配及专属 specs
├── nacos-ai-importer-plugin-ext/         # AI 资源导入插件集合
├── nacos-config-change-plugin-ext/        # 配置变更插件集合
│   ├── nacos-fileformat-config-change-plugin/
│   ├── nacos-webhook-config-change-plugin/
│   └── nacos-whitelist-config-change-plugin/
├── nacos-custom-environment-plugin-ext/   # 自定义环境插件集合
│   └── nacos-db-password-encryption-plugin/
├── nacos-datasource-plugin-ext/           # 数据源扩展插件集合
│   ├── nacos-datasource-plugin-ext-base/
│   ├── nacos-dm-datasource-plugin-ext/
│   ├── nacos-kingbase-datasource-plugin-ext/
│   ├── nacos-mssql-datasource-plugin-ext/
│   ├── nacos-oceanbase-datasource-plugin-ext/
│   ├── nacos-opengauss-datasource-plugin-ext/
│   ├── nacos-oracle-datasource-plugin-ext/
│   ├── nacos-xuguDB-datasource-plugin-ext/
│   └── nacos-yashan-datasource-plugin-ext/
├── nacos-encryption-plugin-ext/           # 加密插件集合
│   └── nacos-aes-encryption-plugin/
└── nacos-trace-plugin-ext/                # 追踪日志插件集合
    └── nacos-trace-logging-plugin/
```

### 4.2 依赖管理

项目统一在父 POM 中管理 Nacos 相关依赖版本

各子模块根据需要的功能引入对应的 Nacos 插件依赖：
- `nacos-config-plugin`: 配置变更相关功能
- `nacos-custom-environment-plugin`: 自定义环境相关功能
- `nacos-encryption-plugin`: 加密相关功能
- `nacos-trace-plugin`: 追踪日志相关功能
- `nacos-datasource-plugin`: 数据源扩展相关功能

### 4.3 打包配置

项目使用 Maven Shade Plugin 进行打包，会自动处理依赖并生成可部署的 JAR 包。打包时会自动排除不必要的文件（如 NOTICE、LICENSE 等）。

## 五、注意事项

1. **版本兼容性**：请确保插件版本与 Nacos 版本匹配，否则可能导致兼容性问题
2. **依赖冲突**：部分插件可能引入额外的第三方依赖，请注意检查是否与 Nacos 或其他插件存在依赖冲突
3. **部署顺序**：建议先部署基础插件（如 datasource-plugin-ext-base），再部署具体数据库实现插件
4. **测试验证**：在生产环境使用前，建议在测试环境充分验证插件功能

## 六、技术支持

如有问题或建议，欢迎通过以下方式联系：

- GitHub Issues: https://github.com/nacos-group/nacos-plugin/issues

## 七、许可证

Apache License, Version 2.0

http://www.apache.org/licenses/LICENSE-2.0
