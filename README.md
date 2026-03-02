# nacos-plugin
A collection of Nacos plug-ins that provide pluggable plug-in capabilities for Nacos and support user customization and high scalability

![](https://tva1.sinaimg.cn/large/008i3skNly1gxmnilyukqj30qp0fgglx.jpg)

## 一、版本映射关系

本插件项目与 Nacos 版本的对应关系如下：

| 插件 Tag 版本 | 支持的 Nacos 版本 |
|-------------|----------------|
| 2.2.x       | Nacos 2.1.x ~ 2.2.x |
| 2.3.x       | Nacos 2.3.x |
| 3.1.x       | Nacos 3.0.x ~ 3.1.x |

**注意**：请选择与您使用的 Nacos 版本相匹配的插件版本进行安装。

## 二、安装说明

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

## 三、插件列表

### 3.1 数据源扩展插件 (nacos-datasource-plugin-ext)

提供多种数据库适配插件，支持 Nacos 使用不同的数据库作为后端存储。

**子插件列表**：
- **nacos-datasource-plugin-ext-base**: 数据库插件基础抽象模块
- **nacos-dm-datasource-plugin-ext**: 达梦数据库适配插件
- **nacos-kingbase-datasource-plugin-ext**: 人大金仓数据库适配插件
- **nacos-mssql-datasource-plugin-ext**: SQL Server 数据库适配插件
- **nacos-oceanbase-datasource-plugin-ext**: OceanBase 数据库适配插件
- **nacos-opengauss-datasource-plugin-ext**: openGauss 数据库适配插件
- **nacos-oracle-datasource-plugin-ext**: Oracle 数据库适配插件
- **nacos-postgresql-datasource-plugin-ext**: PostgreSQL 数据库适配插件
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

## 四、开发指南

### 4.1 项目结构

```
nacos-plugin/
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
│   ├── nacos-postgresql-datasource-plugin-ext/
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
