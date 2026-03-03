# Kingbase 插件 PostgreSQL 兼容模式修复说明

## 📋 修复概述

本次修复将 Kingbase（人大金仓）数据库插件从 MySQL 兼容模式改为 PostgreSQL 兼容模式，以符合 Kingbase 数据库的默认和推荐使用方式。

## 🔧 修改内容

### 1. SQL 初始化脚本修改

**文件路径**: `schema/nacos-kingbase.sql`

**主要变更**:
- ✅ 移除 MySQL 特有的反引号 `` ` ``，改用双引号或不使用引号
- ✅ 将 `AUTO_INCREMENT` 改为 `bigserial` 类型
- ✅ 将 `datetime` 改为 `timestamp(6)`
- ✅ 将 `longtext` 改为 `text`
- ✅ 将 `UNIQUE KEY` 改为 `CREATE UNIQUE INDEX`
- ✅ 注释语法从 `COMMENT='xxx'` 改为 `COMMENT ON COLUMN/TABLE`
- ✅ 添加完整的索引和主键定义

**示例对比**:
```sql
-- ❌ 原 MySQL 语法
CREATE TABLE `config_info` (
    `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT 'id',
    UNIQUE KEY `uk_configinfo_datagrouptenant` (`data_id`,`group_id`,`tenant_id`)
) COMMENT='config_info';

-- ✅ 新 PostgreSQL 语法
CREATE TABLE "config_info" (
  "id" bigserial NOT NULL,
  "data_id" varchar(255)  NOT NULL,
  ...
);
COMMENT ON COLUMN "config_info"."id" IS 'id';
CREATE UNIQUE INDEX "uk_configinfo_datagrouptenant" ON "config_info" ("data_id","group_id","tenant_id");
```

### 2. Mapper 文件修改

#### 2.1 ConfigInfoMapperByKingbase.java

**文件路径**: `impl/kingbase/ConfigInfoMapperByKingbase.java`

**变更内容**:
- ✅ `GROUP_CONCAT(b.tag_name SEPARATOR ',')` → `STRING_AGG(DISTINCT b.tag_name, ',')`
- 涉及行数：2 处（第 218 行、第 282 行）

**示例对比**:
```java
// ❌ 原 MySQL 语法
"GROUP_CONCAT(b.tag_name SEPARATOR ',') as config_tags"

// ✅ 新 PostgreSQL 语法
"STRING_AGG(DISTINCT b.tag_name, ',') as config_tags"
```

#### 2.2 ConfigTagsRelationMapperByKingbase.java

**文件路径**: `impl/kingbase/ConfigTagsRelationMapperByKingbase.java`

**变更内容**:
- ✅ `GROUP_CONCAT(DISTINCT d.tag_name SEPARATOR ',')` → `STRING_AGG(DISTINCT d.tag_name, ',')`
- ✅ `LIMIT offset,size` → `LIMIT size OFFSET offset`
- 涉及行数：2 处（第 82 行、第 142 行）

**示例对比**:
```java
// ❌ 原 MySQL 分页语法
"LIMIT " + context.getStartRow() + "," + context.getPageSize()

// ✅ 新 PostgreSQL 分页语法
"LIMIT " + context.getPageSize() + " OFFSET " + context.getStartRow()
```

### 3. README 文档更新

**文件路径**: `README.md`

**新增内容**:
- ✅ 醒目的升级提示横幅（⚠️⚠️⚠️）
- ✅ 重大变更说明（版本、影响范围、原因）
- ✅ 两种升级方案的详细步骤指南
  - 方案一：迁移到 PostgreSQL 兼容模式（推荐）
  - 方案二：继续使用 MySQL 兼容模式
- ✅ 常见问题解答（Q1-Q3）
- ✅ JDBC 配置示例更新
- ✅ 注意事项说明

**文档结构**:
```markdown
# 标题
## ⚠️⚠️⚠️ 重要升级提示（已使用用户必读）
### 🔴 重大变更说明
### 📋 升级操作指南
#### 方案一：迁移到 PostgreSQL 兼容模式（推荐）
#### 方案二：继续使用 MySQL 兼容模式
### ❓ 常见问题
---
## 原有内容...
```

## 📊 影响评估

### 受影响的用户群体

1. **新用户（无影响）**
   - 直接使用新的 PostgreSQL 兼容模式
   - 按照更新后的 README 配置即可

2. **现有用户（需要关注）**
   - 正在使用 `compatibleMode=mysql` 的用户
   - 需要根据 README 中的指南进行迁移或保持原有配置

### 兼容性说明

| 项目 | MySQL 兼容模式 | PostgreSQL 兼容模式 |
|------|--------------|-------------------|
| JDBC 配置 | `&compatibleMode=mysql` | 无需此参数 |
| SQL 语法 | MySQL方言 | PostgreSQL方言 |
| 自增列 | AUTO_INCREMENT | bigserial |
| 字符串聚合 | GROUP_CONCAT | STRING_AGG |
| 分页 | LIMIT offset,size | LIMIT size OFFSET |
| 引用符 | 反引号 `` ` `` | 双引号 `"` |

## 🎯 验证清单

### 开发阶段验证
- [x] SQL 脚本语法正确性
- [x] Mapper 文件函数替换
- [x] README 文档完整性

### 部署前验证（建议用户执行）
- [ ] 备份现有数据库
- [ ] 修改 JDBC 连接配置
- [ ] 执行新的初始化脚本
- [ ] 数据迁移（如需要）
- [ ] 启动 Nacos 验证功能
- [ ] 检查配置管理功能
- [ ] 检查权限管理功能
- [ ] 性能测试

## 📚 参考资料

- KingbaseES 官方文档：https://www.kingbase.com.cn/
- PostgreSQL STRING_AGG 函数：https://www.postgresql.org/docs/current/functions-aggregate.html
- Nacos 多数据源插件设计：https://nacos.io/zh-cn/docs/v2/plugin/datasource.html

## 💡 后续建议

1. **提供迁移工具**
   - 开发自动化数据迁移脚本
   - 提供 MySQL → PostgreSQL模式迁移向导

2. **完善测试用例**
   - 增加 PostgreSQL模式的集成测试
   - 提供性能对比报告

3. **持续监控**
   - 收集用户迁移反馈
   - 优化迁移文档和工具

## 📞 联系方式

如有问题，请通过以下方式联系：
- GitHub Issues: https://github.com/nacos-group/nacos-plugin/issues
- 官方文档：https://nacos.io/
