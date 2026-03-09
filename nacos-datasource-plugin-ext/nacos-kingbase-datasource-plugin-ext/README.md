# Nacos 数据库 Kingbase 适配插件

## ⚠️⚠️⚠️ 重要升级提示（已使用用户必读）

> **如果您已经在生产环境使用本插件，请务必仔细阅读以下内容！**

### 🔴 重大变更说明

**版本：3.1.x 2026-03-03 起**

- **变更内容**：数据库初始化脚本从 **MySQL 兼容模式** 改为 **PostgreSQL 兼容模式**
- **影响范围**：所有正在使用 `compatibleMode=mysql` 配置的用户
- **原因说明**：Kingbase（人大金仓）基于 PostgreSQL 内核开发，默认推荐使用 PostgreSQL 兼容模式

### 📋 升级操作指南

#### 方案一：迁移到 PostgreSQL 兼容模式（推荐）

**适用场景**：新建系统或愿意进行数据迁移的用户

**步骤：**

1. **备份现有数据**
   ```bash
   # 使用 kingbase 导出工具备份当前数据库
   sys_dump -U SYSDBA -f nacos_backup.sql nacos
   ```

2. **修改 JDBC 连接配置**
   ```properties
   # 移除 compatibleMode=mysql 参数
   spring.datasource.platform=kingbase
   db.url.0=jdbc:kingbase8://127.0.0.1:54321/kingbase?schema=NACOS&ignoreCase=true&ENCODING=utf-8
   db.user.0=SYSDBA
   db.password.0=SYSDBA
   db.pool.config.driverClassName=com.kingbase8.Driver
   ```

3. **使用新的初始化脚本**
   ```bash
   # 在新的 schema 中执行
   ksql -U SYSDBA -d kingbase -f schema/nacos-kingbase.sql
   ```

4. **数据迁移**
   - 使用 kingbase 数据迁移工具（KDTS）进行数据迁移
   - 或手动导出导入数据

5. **验证测试**
   - 启动 Nacos 验证功能
   - 检查配置管理、权限管理等功能是否正常

#### 方案二：继续使用 MySQL 兼容模式

**适用场景**：暂时无法迁移的生产环境

**步骤：**

1. **保留原有 JDBC 配置**
   ```properties
   # 保持 compatibleMode=mysql 参数
   db.url.0=jdbc:kingbase8://127.0.0.1:54321/kingbase?schema=NACOS&compatibleMode=mysql&ignoreCase=true&ENCODING=utf-8
   ```

2. **使用旧版 SQL 脚本备份**
   ```bash
   # 从 Git 历史中获取旧版 nacos-kingbase.sql
   git show <commit-id>:nacos-kingbase.sql > nacos-kingbase-mysql.sql
   ```

3. **后续计划**
   - 评估迁移到 PostgreSQL 兼容模式的时间表
   - 关注官方发布的迁移工具

### ❓ 常见问题

**Q1: 如何判断我当前使用的是哪种模式？**  
A: 检查 JDBC 连接字符串中是否包含 `compatibleMode=mysql` 参数

**Q2: 不升级会有什么影响？**  
A: 短期无影响，但建议使用 PostgreSQL 兼容模式以获得更好的性能和兼容性

**Q3: 数据迁移复杂吗？**  
A: 可使用 kingbase 官方迁移工具 KDTS，具体参考官方文档

---

## 一、注意事项

### 1.1、修改数据库配置文件

在 application.properties 文件中声明 kingbase 的配置信息：

```properties
spring.datasource.platform=kingbase
# PostgreSQL 兼容模式（默认推荐）- 移除 compatibleMode=mysql
db.url.0=jdbc:kingbase8://127.0.0.1:54321/kingbase?schema=NACOS&ignoreCase=true&ENCODING=utf-8
db.user.0=SYSDBA
db.password.0=SYSDBA
db.pool.config.driverClassName=com.kingbase8.Driver
```

### 1.2、增加 kingbase 数据库驱动


```xml
<dependency>
    <groupId>cn.com.kingbase</groupId>
    <artifactId>kingbase8</artifactId>
    <version>8.6.0</version>
</dependency>
```

### 1.3、表结构初始化

在 nacos 数据库中执行 schema/nacos-kingbase.sql 文件

**注意**：此脚本为 PostgreSQL 兼容模式，如需要使用 MySQL 兼容模式，请查看上方的升级指南。
