# Nacos OceanBase Oracle 模式数据源插件

## 📖 简介

本插件为 Nacos 提供 OceanBase Oracle 模式的数据源支持。OceanBase 数据库支持 MySQL 和 Oracle 两种兼容模式，本插件专门针对 **Oracle 兼容模式** 进行了适配，实现了完整的 Oracle SQL 语法支持。

## ✨ 特性

- ✅ 完整支持 OceanBase Oracle 模式的 SQL 语法
- ✅ 使用 Oracle 标准分页语法（OFFSET ROWS FETCH NEXT）
- ✅ 支持 Oracle 函数（NVL、SYSTIMESTAMP 等）
- ✅ 完整实现 Nacos 所需的所有 Mapper
- ✅ 基于 OceanBase JDBC 驱动 2.4.3
- ✅ 兼容 Nacos 2.4.3 版本

## 🏗️ 架构说明

### 核心组件

```
nacos-oceanbase-datasource-plugin-ext/
├── src/main/java/
│   └── com/alibaba/nacos/plugin/datasource/
│       ├── dialect/
│       │   └── OceanbaseDatabaseDialect.java          # Oracle 语法方言
│       ├── enums/
│       │   └── TrustedOceanbaseFunctionEnum.java      # 可信函数映射
│       └── impl/oceanbase/
│           ├── AbstractOceanbaseMapper.java           # 抽象基类
│           ├── ConfigInfoMapperByOceanbase.java       # 配置信息
│           ├── ConfigInfoAggrMapperByOceanbase.java   # 聚合配置
│           ├── ConfigTagsRelationMapperByOceanbase.java # 标签关系
│           ├── HistoryConfigInfoMapperOceanbase.java  # 历史配置
│           ├── GroupCapacityMapperByOceanbase.java    # 分组容量
│           ├── TenantCapacityMapperByOceanbase.java   # 租户容量
│           └── TenantInfoMapperByOceanbase.java       # 租户信息
└── src/main/resources/META-INF/services/              # SPI 配置
```

### Oracle 语法适配

| MySQL 语法 | Oracle 语法 | 说明 |
|-----------|------------|------|
| `LIMIT ?` | `FETCH FIRST ? ROWS ONLY` | 限制返回行数 |
| `LIMIT ?, ?` | `OFFSET ? ROWS FETCH NEXT ? ROWS ONLY` | 分页查询 |
| `IFNULL(?, ?)` | `NVL(?, ?)` | 空值处理 |
| `NOW()` | `SYSTIMESTAMP` | 当前时间 |

## 🚀 快速开始

### 前置条件

1. Nacos 2.4.3
2. OceanBase 数据库（Oracle 模式）
3. Java 8 或更高版本

### 安装步骤

#### 1. 编译插件

```bash
cd nacos-datasource-plugin-ext
mvn clean install -pl nacos-datasource-plugin-ext-base,nacos-oceanbase-datasource-plugin-ext -am -DskipTests
```

编译成功后，会在 `target` 目录下生成插件 JAR 包：
```
nacos-oceanbase-datasource-plugin-ext-{version}.jar
```

#### 2. 部署插件

将编译好的 JAR 包复制到 Nacos 服务器的插件目录：

```bash
# Nacos 插件目录结构
${nacos.home}/plugins/
└── datasource/
    └── nacos-oceanbase-datasource-plugin-ext-{version}.jar
```

**注意**：如果 `plugins/datasource` 目录不存在，请手动创建。

#### 3. 初始化数据库

在 OceanBase Oracle 模式下执行 Nacos 初始化脚本：

```bash
# 使用 Nacos 提供的 Oracle 初始化脚本
# 注意：需要使用 Oracle 语法的 SQL 脚本
obclient -h <oceanbase-host> -P <port> -u <username> -p < nacos-oracle.sql
```

**重要提示**：
- OceanBase Oracle 模式需要使用 Oracle 兼容的 DDL 语句
- 确保租户已设置为 Oracle 模式
- 表名和字段名可能需要大写或加引号

#### 4. 配置 Nacos

编辑 `${nacos.home}/conf/application.properties`：

```properties
### 使用外部数据源
spring.datasource.platform=oceanbase

### OceanBase Oracle 模式连接配置
db.url.0=jdbc:oceanbase://<host>:<port>/<database>?useUnicode=true&characterEncoding=utf8&serverTimezone=Asia/Shanghai
db.user.0=<username>
db.password.0=<password>

### 连接池配置（可选）
db.pool.config.connectionTimeout=30000
db.pool.config.validationTimeout=10000
db.pool.config.maximumPoolSize=20
db.pool.config.minimumIdle=5
```

**连接示例**：
```properties
# 示例配置
db.url.0=jdbc:oceanbase://192.168.1.100:2881/nacos?useUnicode=true&characterEncoding=utf8
db.user.0=nacos@tenant#cluster
db.password.0=nacos123
```

#### 5. 启动 Nacos

```bash
cd ${nacos.home}/bin
./startup.sh -m standalone
```

查看日志确认插件加载：
```bash
tail -f ${nacos.home}/logs/nacos.log
```

期望看到类似日志：
```
[DatabaseDialectManager] Load DatabaseDialect(oceanbase) OceanbaseDatabaseDialect successfully.
```

## 🔧 高级配置

### 1. 多数据源配置

OceanBase 支持配置多个数据源实现高可用：

```properties
db.num=2
db.url.0=jdbc:oceanbase://node1:2881/nacos
db.url.1=jdbc:oceanbase://node2:2881/nacos
db.user.0=nacos@tenant#cluster
db.user.1=nacos@tenant#cluster
db.password.0=password
db.password.1=password
```

### 2. 连接池优化

针对 OceanBase 的连接池推荐配置：

```properties
# HikariCP 配置
db.pool.config.connectionTimeout=30000
db.pool.config.validationTimeout=10000
db.pool.config.maximumPoolSize=30
db.pool.config.minimumIdle=10
db.pool.config.idleTimeout=600000
db.pool.config.maxLifetime=1800000
```

### 3. OceanBase 特定参数

```properties
# 启用 OceanBase 负载均衡
db.url.0=jdbc:oceanbase://host:port/database?loadBalanceStrategy=rotation

# 启用连接池监控
db.url.0=jdbc:oceanbase://host:port/database?useServerPrepStmts=true&cachePrepStmts=true
```

## 🧪 验证测试

### 1. 测试数据库连接

```bash
# 使用 OceanBase 客户端测试
obclient -h <host> -P <port> -u <username> -p -D <database>

# 测试查询
SELECT * FROM config_info FETCH FIRST 10 ROWS ONLY;
```

### 2. 验证插件加载

访问 Nacos 控制台：
```
http://localhost:8848/nacos
```

检查以下功能：
- ✅ 配置管理 - 创建、修改、删除配置
- ✅ 服务管理 - 注册、发现服务
- ✅ 命名空间 - 创建、切换命名空间
- ✅ 集群管理 - 查看节点状态

### 3. SQL 语法验证

启用 SQL 日志查看实际执行的 SQL：

```properties
# application.properties
logging.level.com.alibaba.nacos.config.server.service=DEBUG
```

期望看到 Oracle 语法的 SQL：
```sql
SELECT * FROM config_info WHERE tenant_id = NVL(?, 'PUBLIC') OFFSET 0 ROWS FETCH NEXT 10 ROWS ONLY
```

## 📊 性能调优

### 1. OceanBase 参数优化

```sql
-- 调整租户内存（根据实际情况）
ALTER RESOURCE UNIT unit_name MEMORY_SIZE '4G';

-- 优化并行度
ALTER SYSTEM SET parallel_servers_target=128;
```

### 2. 索引优化

确保关键表有适当的索引：

```sql
-- 配置信息表索引
CREATE INDEX idx_dataid ON config_info(data_id, group_id, tenant_id);
CREATE INDEX idx_gmt_modified ON config_info(gmt_modified);

-- 历史配置表索引
CREATE INDEX idx_his_dataid ON his_config_info(data_id, group_id, tenant_id);
```

### 3. 连接池调优

根据业务负载调整：

| 场景 | maximumPoolSize | minimumIdle |
|------|----------------|-------------|
| 轻量级（< 1000 QPS） | 10 | 5 |
| 中等负载（1000-5000 QPS） | 20 | 10 |
| 高负载（> 5000 QPS） | 50 | 20 |

## 🐛 故障排查

### 常见问题

#### 1. 插件未加载

**症状**：启动日志中找不到 OceanBase 插件加载信息

**解决方案**：
```bash
# 检查插件文件是否存在
ls -l ${nacos.home}/plugins/datasource/

# 检查 JAR 包中的 SPI 配置
jar tf nacos-oceanbase-datasource-plugin-ext-*.jar | grep META-INF/services

# 查看 Nacos 启动日志
grep -i "oceanbase\|DatabaseDialect" ${nacos.home}/logs/nacos.log
```

#### 2. SQL 语法错误

**症状**：日志中出现 SQL 语法错误

**常见错误**：
```
ORA-00933: SQL command not properly ended
```

**解决方案**：
- 确认 OceanBase 租户模式为 Oracle（不是 MySQL）
- 检查 `spring.datasource.platform=oceanbase` 配置正确
- 验证插件 JAR 包是否正确部署

#### 3. 连接失败

**症状**：无法连接到 OceanBase

**检查清单**：
```bash
# 1. 测试网络连通性
telnet <oceanbase-host> <port>

# 2. 验证用户名密码
obclient -h <host> -P <port> -u <username> -p

# 3. 检查租户和集群名称
# 格式：username@tenant#cluster
db.user.0=nacos@nacos_tenant#test_cluster

# 4. 查看 OceanBase 日志
tail -f /data/observer/log/observer.log
```

#### 4. 性能问题

**症状**：查询响应慢

**诊断步骤**：
```sql
-- 查看慢查询
SELECT * FROM GV$OB_SQL_AUDIT WHERE elapsed_time > 1000000;

-- 查看执行计划
EXPLAIN SELECT * FROM config_info WHERE data_id = 'test';

-- 检查统计信息
SELECT * FROM DBA_TAB_STATISTICS WHERE table_name = 'CONFIG_INFO';
```

## 🔒 安全建议

1. **数据库用户权限**：
   ```sql
   -- 创建专用数据库用户
   CREATE USER nacos IDENTIFIED BY '<strong_password>';

   -- 授予必要权限
   GRANT SELECT, INSERT, UPDATE, DELETE ON nacos.* TO nacos;
   ```

2. **密码加密**：
   使用 Jasypt 加密数据库密码
   ```properties
   jasypt.encryptor.password=your-secret-key
   db.password.0=ENC(encrypted_password)
   ```

3. **SSL/TLS 连接**：
   ```properties
   db.url.0=jdbc:oceanbase://host:port/database?useSSL=true&requireSSL=true
   ```

## 📚 参考文档

- [Nacos 官方文档](https://nacos.io/zh-cn/docs/quick-start.html)
- [OceanBase 官方文档](https://www.oceanbase.com/docs)
- [OceanBase Oracle 模式指南](https://www.oceanbase.com/docs/oracle-mode)
- [Nacos 数据源插件开发](https://nacos.io/zh-cn/docs/plugin.html)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 开发环境

```bash
# 克隆项目
git clone https://github.com/alibaba/nacos-plugin.git
cd nacos-plugin/nacos-datasource-plugin-ext/nacos-oceanbase-datasource-plugin-ext

# 编译
mvn clean install

# 运行测试
mvn test
```

### 提交规范

- feat: 新功能
- fix: 修复 bug
- docs: 文档更新
- test: 测试相关
- refactor: 重构代码

## 📄 许可证

Apache License 2.0

## 💬 社区支持

- Nacos 社区：https://github.com/alibaba/nacos/discussions
- OceanBase 社区：https://github.com/oceanbase/oceanbase/discussions
- 钉钉群：搜索群号加入 Nacos 社区交流群

---

**注意**：本插件专门为 OceanBase **Oracle 模式**设计。如果您使用的是 OceanBase MySQL 模式，请使用 MySQL 数据源插件。
