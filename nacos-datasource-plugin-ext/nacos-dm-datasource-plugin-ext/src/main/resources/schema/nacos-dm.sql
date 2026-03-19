/*
 * Copyright 1999-2018 Alibaba Group Holding Ltd.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */


-- =====================================================
-- 验证版本Nacos 2.5.1 达梦8
-- 适用场景：全新安装，数据库中没有 Nacos 相关表
-- 注意：若表已存在，执行会报错，请勿在已有数据的库上直接运行！
-- =====================================================


-- 删除已存在的表（注意顺序，先删除有依赖关系的表）
DROP TABLE IF EXISTS permissions CASCADE;
DROP TABLE IF EXISTS roles CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS his_config_info CASCADE;
DROP TABLE IF EXISTS config_tags_relation CASCADE;
DROP TABLE IF EXISTS config_info_gray CASCADE;
DROP TABLE IF EXISTS config_info CASCADE;
DROP TABLE IF EXISTS group_capacity CASCADE;
DROP TABLE IF EXISTS tenant_capacity CASCADE;
DROP TABLE IF EXISTS tenant_info CASCADE;


CREATE TABLE config_info (
                             id BIGINT NOT NULL IDENTITY(1,1) ,
                             data_id VARCHAR(255) NOT NULL,
                             group_id VARCHAR(128),
                             content CLOB NOT NULL,
                             md5 VARCHAR(32),
                             gmt_create DATETIME DEFAULT CURRENT_TIMESTAMP,
                             gmt_modified DATETIME DEFAULT CURRENT_TIMESTAMP,
                             src_user CLOB,
                             src_ip VARCHAR(50),
                             app_name VARCHAR(128),
                             tenant_id VARCHAR(128) DEFAULT '',
                             c_desc VARCHAR(256),
                             c_use VARCHAR(64),
                             effect VARCHAR(64),
                             type VARCHAR(64),
                             c_schema CLOB,
                             encrypted_data_key VARCHAR(1024) DEFAULT '',
                             PRIMARY KEY(id)
);
COMMENT ON TABLE config_info IS 'config_info';
COMMENT ON COLUMN config_info.id IS 'id';
COMMENT ON COLUMN config_info.data_id IS 'data_id';
COMMENT ON COLUMN config_info.group_id IS 'group_id';
COMMENT ON COLUMN config_info.content IS 'content';
COMMENT ON COLUMN config_info.md5 IS 'md5';
COMMENT ON COLUMN config_info.gmt_create IS '创建时间';
COMMENT ON COLUMN config_info.gmt_modified IS '修改时间';
COMMENT ON COLUMN config_info.src_user IS 'source user';
COMMENT ON COLUMN config_info.src_ip IS 'source ip';
COMMENT ON COLUMN config_info.app_name IS 'app_name';
COMMENT ON COLUMN config_info.tenant_id IS '租户字段';
COMMENT ON COLUMN config_info.c_desc IS 'configuration description';
COMMENT ON COLUMN config_info.c_use IS 'configuration usage';
COMMENT ON COLUMN config_info.effect IS '配置生效的描述';
COMMENT ON COLUMN config_info.type IS '配置的类型';
COMMENT ON COLUMN config_info.c_schema IS '配置的模式';
COMMENT ON COLUMN config_info.encrypted_data_key IS '密钥';

CREATE UNIQUE INDEX uk_configinfo_datagrouptenant ON config_info(data_id, group_id, tenant_id);

/******************************************/
/*   表名称 = config_info_gray  since 2.5.0 */
/******************************************/
CREATE TABLE config_info_gray (
                                  id BIGINT NOT NULL IDENTITY(1,1),
                                  data_id VARCHAR(255) NOT NULL,
                                  group_id VARCHAR(128) NOT NULL,
                                  content CLOB NOT NULL,
                                  md5 VARCHAR(32),
                                  src_user CLOB,
                                  src_ip VARCHAR(100),
                                  gmt_create DATETIME DEFAULT CURRENT_TIMESTAMP,
                                  gmt_modified DATETIME DEFAULT CURRENT_TIMESTAMP,
                                  app_name VARCHAR(128),
                                  tenant_id VARCHAR(128) DEFAULT '',
                                  gray_name VARCHAR(128) NOT NULL,
                                  gray_rule CLOB NOT NULL,
                                  encrypted_data_key VARCHAR(256) DEFAULT '',
                                  PRIMARY KEY(id)
);
COMMENT ON TABLE config_info_gray IS 'config_info_gray';
COMMENT ON COLUMN config_info_gray.id IS 'id';
COMMENT ON COLUMN config_info_gray.data_id IS 'data_id';
COMMENT ON COLUMN config_info_gray.group_id IS 'group_id';
COMMENT ON COLUMN config_info_gray.content IS 'content';
COMMENT ON COLUMN config_info_gray.md5 IS 'md5';
COMMENT ON COLUMN config_info_gray.src_user IS 'src_user';
COMMENT ON COLUMN config_info_gray.src_ip IS 'src_ip';
COMMENT ON COLUMN config_info_gray.gmt_create IS 'gmt_create';
COMMENT ON COLUMN config_info_gray.gmt_modified IS 'gmt_modified';
COMMENT ON COLUMN config_info_gray.app_name IS 'app_name';
COMMENT ON COLUMN config_info_gray.tenant_id IS 'tenant_id';
COMMENT ON COLUMN config_info_gray.gray_name IS 'gray_name';
COMMENT ON COLUMN config_info_gray.gray_rule IS 'gray_rule';
COMMENT ON COLUMN config_info_gray.encrypted_data_key IS 'encrypted_data_key';

CREATE UNIQUE INDEX uk_configinfogray_datagrouptenantgray ON config_info_gray(data_id, group_id, tenant_id, gray_name);
CREATE INDEX idx_dataid_gmt_modified ON config_info_gray(data_id, gmt_modified);
CREATE INDEX idx_gmt_modified ON config_info_gray(gmt_modified);

/******************************************/
/*   表名称 = config_tags_relation         */
/******************************************/
CREATE TABLE config_tags_relation (
                                      id BIGINT NOT NULL,
                                      tag_name VARCHAR(128) NOT NULL,
                                      tag_type VARCHAR(64),
                                      data_id VARCHAR(255) NOT NULL,
                                      group_id VARCHAR(128) NOT NULL,
                                      tenant_id VARCHAR(128) DEFAULT '',
                                      nid BIGINT NOT NULL IDENTITY(1,1),
                                      PRIMARY KEY(nid)
);
COMMENT ON TABLE config_tags_relation IS 'config_tag_relation';
COMMENT ON COLUMN config_tags_relation.id IS 'id';
COMMENT ON COLUMN config_tags_relation.tag_name IS 'tag_name';
COMMENT ON COLUMN config_tags_relation.tag_type IS 'tag_type';
COMMENT ON COLUMN config_tags_relation.data_id IS 'data_id';
COMMENT ON COLUMN config_tags_relation.group_id IS 'group_id';
COMMENT ON COLUMN config_tags_relation.tenant_id IS 'tenant_id';
COMMENT ON COLUMN config_tags_relation.nid IS 'nid, 自增长标识';

CREATE UNIQUE INDEX uk_configtagrelation_configidtag ON config_tags_relation(id, tag_name, tag_type);
CREATE INDEX idx_tenant_id ON config_tags_relation(tenant_id);

/******************************************/
/*   表名称 = group_capacity               */
/******************************************/
CREATE TABLE group_capacity (
                                id BIGINT NOT NULL IDENTITY(1,1) ,
                                group_id VARCHAR(128) NOT NULL DEFAULT '',
                                quota INT DEFAULT 0,
                                usage INT DEFAULT 0,
                                max_size INT DEFAULT 0,
                                max_aggr_count INT DEFAULT 0,
                                max_aggr_size INT DEFAULT 0,
                                max_history_count INT DEFAULT 0,
                                gmt_create DATETIME DEFAULT CURRENT_TIMESTAMP,
                                gmt_modified DATETIME DEFAULT CURRENT_TIMESTAMP,
                                PRIMARY KEY(id)
);
COMMENT ON TABLE group_capacity IS '集群、各Group容量信息表';
COMMENT ON COLUMN group_capacity.id IS '主键ID';
COMMENT ON COLUMN group_capacity.group_id IS 'Group ID，空字符表示整个集群';
COMMENT ON COLUMN group_capacity.quota IS '配额，0表示使用默认值';
COMMENT ON COLUMN group_capacity.usage IS '使用量';
COMMENT ON COLUMN group_capacity.max_size IS '单个配置大小上限，单位为字节，0表示使用默认值';
COMMENT ON COLUMN group_capacity.max_aggr_count IS '聚合子配置最大个数，0表示使用默认值';
COMMENT ON COLUMN group_capacity.max_aggr_size IS '单个聚合数据的子配置大小上限，单位为字节，0表示使用默认值';
COMMENT ON COLUMN group_capacity.max_history_count IS '最大变更历史数量';
COMMENT ON COLUMN group_capacity.gmt_create IS '创建时间';
COMMENT ON COLUMN group_capacity.gmt_modified IS '修改时间';

CREATE UNIQUE INDEX uk_group_id ON group_capacity(group_id);

/******************************************/
/*   表名称 = his_config_info              */
/******************************************/
CREATE TABLE his_config_info (
                                 id BIGINT NOT NULL,
                                 nid BIGINT NOT NULL IDENTITY(1,1),
                                 data_id VARCHAR(255) NOT NULL,
                                 group_id VARCHAR(128) NOT NULL,
                                 app_name VARCHAR(128),
                                 content CLOB NOT NULL,
                                 md5 VARCHAR(32),
                                 gmt_create DATETIME DEFAULT CURRENT_TIMESTAMP,
                                 gmt_modified DATETIME DEFAULT CURRENT_TIMESTAMP,
                                 src_user CLOB,
                                 src_ip VARCHAR(50),
                                 op_type CHAR(10),
                                 tenant_id VARCHAR(128) DEFAULT '',
                                 encrypted_data_key VARCHAR(1024) DEFAULT '',
                                 publish_type VARCHAR(50) DEFAULT 'formal',
                                 gray_name VARCHAR(50),
                                 ext_info CLOB,
                                 PRIMARY KEY(nid)
);
COMMENT ON TABLE his_config_info IS '多租户改造';
COMMENT ON COLUMN his_config_info.id IS 'id';
COMMENT ON COLUMN his_config_info.nid IS 'nid, 自增标识';
COMMENT ON COLUMN his_config_info.data_id IS 'data_id';
COMMENT ON COLUMN his_config_info.group_id IS 'group_id';
COMMENT ON COLUMN his_config_info.app_name IS 'app_name';
COMMENT ON COLUMN his_config_info.content IS 'content';
COMMENT ON COLUMN his_config_info.md5 IS 'md5';
COMMENT ON COLUMN his_config_info.gmt_create IS '创建时间';
COMMENT ON COLUMN his_config_info.gmt_modified IS '修改时间';
COMMENT ON COLUMN his_config_info.src_user IS 'source user';
COMMENT ON COLUMN his_config_info.src_ip IS 'source ip';
COMMENT ON COLUMN his_config_info.op_type IS 'operation type';
COMMENT ON COLUMN his_config_info.tenant_id IS '租户字段';
COMMENT ON COLUMN his_config_info.encrypted_data_key IS '密钥';
COMMENT ON COLUMN his_config_info.publish_type IS 'publish type gray or formal';
COMMENT ON COLUMN his_config_info.gray_name IS 'gray name';
COMMENT ON COLUMN his_config_info.ext_info IS 'ext info';

CREATE INDEX idx_gmt_create ON his_config_info(gmt_create);
CREATE INDEX idx_his_config_info_gmt_modified ON his_config_info(gmt_modified);
CREATE INDEX idx_did ON his_config_info(data_id);

/******************************************/
/*   表名称 = tenant_capacity              */
/******************************************/
CREATE TABLE tenant_capacity (
                                 id BIGINT NOT NULL IDENTITY(1,1),
                                 tenant_id VARCHAR(128) NOT NULL DEFAULT '',
                                 quota INT DEFAULT 0,
                                 usage INT DEFAULT 0,
                                 max_size INT DEFAULT 0,
                                 max_aggr_count INT DEFAULT 0,
                                 max_aggr_size INT DEFAULT 0,
                                 max_history_count INT DEFAULT 0,
                                 gmt_create DATETIME DEFAULT CURRENT_TIMESTAMP,
                                 gmt_modified DATETIME DEFAULT CURRENT_TIMESTAMP,
                                 PRIMARY KEY(id)
);
COMMENT ON TABLE tenant_capacity IS '租户容量信息表';
COMMENT ON COLUMN tenant_capacity.id IS '主键ID';
COMMENT ON COLUMN tenant_capacity.tenant_id IS 'Tenant ID';
COMMENT ON COLUMN tenant_capacity.quota IS '配额，0表示使用默认值';
COMMENT ON COLUMN tenant_capacity.usage IS '使用量';
COMMENT ON COLUMN tenant_capacity.max_size IS '单个配置大小上限，单位为字节，0表示使用默认值';
COMMENT ON COLUMN tenant_capacity.max_aggr_count IS '聚合子配置最大个数';
COMMENT ON COLUMN tenant_capacity.max_aggr_size IS '单个聚合数据的子配置大小上限，单位为字节，0表示使用默认值';
COMMENT ON COLUMN tenant_capacity.max_history_count IS '最大变更历史数量';
COMMENT ON COLUMN tenant_capacity.gmt_create IS '创建时间';
COMMENT ON COLUMN tenant_capacity.gmt_modified IS '修改时间';

CREATE UNIQUE INDEX uk_tenant_id ON tenant_capacity(tenant_id);

/******************************************/
/*   表名称 = tenant_info                  */
/******************************************/
CREATE TABLE tenant_info (
                             id BIGINT NOT NULL IDENTITY(1,1),
                             kp VARCHAR(128) NOT NULL,
                             tenant_id VARCHAR(128) DEFAULT '',
                             tenant_name VARCHAR(128) DEFAULT '',
                             tenant_desc VARCHAR(256),
                             create_source VARCHAR(32),
                             gmt_create BIGINT NOT NULL,
                             gmt_modified BIGINT NOT NULL,
                             PRIMARY KEY(id)
);
COMMENT ON TABLE tenant_info IS 'tenant_info';
COMMENT ON COLUMN tenant_info.id IS 'id';
COMMENT ON COLUMN tenant_info.kp IS 'kp';
COMMENT ON COLUMN tenant_info.tenant_id IS 'tenant_id';
COMMENT ON COLUMN tenant_info.tenant_name IS 'tenant_name';
COMMENT ON COLUMN tenant_info.tenant_desc IS 'tenant_desc';
COMMENT ON COLUMN tenant_info.create_source IS 'create_source';
COMMENT ON COLUMN tenant_info.gmt_create IS '创建时间';
COMMENT ON COLUMN tenant_info.gmt_modified IS '修改时间';

CREATE UNIQUE INDEX uk_tenant_info_kptenantid ON tenant_info(kp, tenant_id);
CREATE INDEX idx_tenant_info_tenant_id ON tenant_info(tenant_id);

/******************************************/
/*   表名称 = users                       */
/******************************************/
CREATE TABLE users (
                       username VARCHAR(50) NOT NULL ,
                       password VARCHAR(500) NOT NULL,
                       enabled BIT NOT NULL,
                       PRIMARY KEY(username)
);
COMMENT ON TABLE users IS 'users';
COMMENT ON COLUMN users.username IS 'username';
COMMENT ON COLUMN users.password IS 'password';
COMMENT ON COLUMN users.enabled IS 'enabled';

/******************************************/
/*   表名称 = roles                       */
/******************************************/
CREATE TABLE roles (
                       username VARCHAR(50) NOT NULL,
                       role VARCHAR(50) NOT NULL
);
COMMENT ON TABLE roles IS 'roles';
COMMENT ON COLUMN roles.username IS 'username';
COMMENT ON COLUMN roles.role IS 'role';

CREATE UNIQUE INDEX idx_user_role ON roles(username, role);

/******************************************/
/*   表名称 = permissions                 */
/******************************************/
CREATE TABLE permissions (
                             role VARCHAR(50) NOT NULL,
                             resource VARCHAR(128) NOT NULL,
                             action VARCHAR(8) NOT NULL
);
COMMENT ON TABLE permissions IS 'permissions';
COMMENT ON COLUMN permissions.role IS 'role';
COMMENT ON COLUMN permissions.resource IS 'resource';
COMMENT ON COLUMN permissions.action IS 'action';

CREATE UNIQUE INDEX uk_role_permission ON permissions(role, resource, action);