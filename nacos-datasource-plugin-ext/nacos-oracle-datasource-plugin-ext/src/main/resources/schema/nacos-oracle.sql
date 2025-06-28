/*
 * Copyright 1999-2023 Alibaba Group Holding Ltd.
 *
 * Licensed under the Apache License, Version 2.0 (the License);
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an AS IS BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

-- ----------------------------
-- Table structure for config_info
-- ----------------------------
BEGIN
EXECUTE IMMEDIATE 'DROP TABLE config_info';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -942 THEN
         RAISE;
END IF;
END;
CREATE TABLE config_info (
                             id NUMBER(20) PRIMARY KEY,
                             data_id VARCHAR2(255) NOT NULL,
                             group_id VARCHAR2(128) DEFAULT NULL,
                             content CLOB NOT NULL,
                             md5 VARCHAR2(32) DEFAULT NULL,
                             gmt_create TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                             gmt_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                             src_user CLOB,
                             src_ip VARCHAR2(50) DEFAULT NULL,
                             app_name VARCHAR2(128) DEFAULT NULL,
                             tenant_id VARCHAR2(128) DEFAULT '',
                             c_desc VARCHAR2(256) DEFAULT NULL,
                             c_use VARCHAR2(64) DEFAULT NULL,
                             effect VARCHAR2(64) DEFAULT NULL,
                             type VARCHAR2(64) DEFAULT NULL,
                             c_schema CLOB,
                             encrypted_data_key VARCHAR2(1024) DEFAULT '' NOT NULL
);

CREATE UNIQUE INDEX uk_configinfo_datagrouptenant ON config_info (data_id, group_id, tenant_id);

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

CREATE SEQUENCE config_info_seq START WITH 1 INCREMENT BY 1 NOCACHE;

CREATE OR REPLACE TRIGGER config_info_trg
BEFORE INSERT ON config_info
FOR EACH ROW
BEGIN
    :new.id := config_info_seq.NEXTVAL;
END;
-- ----------------------------
-- 表名称 = config_info_gray
-- ----------------------------
BEGIN
EXECUTE IMMEDIATE 'DROP TABLE config_info_gray';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -942 THEN
         RAISE;
END IF;
END;
CREATE TABLE config_info_gray (
                                  id NUMBER(20) PRIMARY KEY,
                                  data_id VARCHAR2(255) NOT NULL,
                                  group_id VARCHAR2(128) NOT NULL,
                                  content CLOB NOT NULL,
                                  md5 VARCHAR2(32) DEFAULT NULL,
                                  src_user CLOB,
                                  src_ip VARCHAR2(100) DEFAULT NULL,
                                  gmt_create TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP NOT NULL,
                                  gmt_modified TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP NOT NULL,
                                  app_name VARCHAR2(128) DEFAULT NULL,
                                  tenant_id VARCHAR2(128) DEFAULT '',
                                  gray_name VARCHAR2(128) NOT NULL,
                                  gray_rule CLOB NOT NULL,
                                  encrypted_data_key VARCHAR2(256) DEFAULT '' NOT NULL
);

CREATE UNIQUE INDEX uk_configinfogray_datagrouptenantgray ON config_info_gray (data_id, group_id, tenant_id, gray_name);
CREATE INDEX idx_dataid_gmt_modified_gray ON config_info_gray (data_id, gmt_modified);
CREATE INDEX idx_gmt_modified_gray ON config_info_gray (gmt_modified);

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

CREATE SEQUENCE config_info_gray_seq START WITH 1 INCREMENT BY 1 NOCACHE;

CREATE OR REPLACE TRIGGER config_info_gray_trg
BEFORE INSERT ON config_info_gray
FOR EACH ROW
BEGIN
    :new.id := config_info_gray_seq.NEXTVAL;
END;

-- ----------------------------
-- Table structure for config_info_beta
-- ----------------------------
BEGIN
EXECUTE IMMEDIATE 'DROP TABLE config_info_beta';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -942 THEN
         RAISE;
END IF;
END;
CREATE TABLE config_info_beta (
                                  id int NOT NULL,
                                  data_id varchar2(255)  NOT NULL,
                                  group_id varchar2(128)  NOT NULL,
                                  app_name varchar2(128) ,
                                  content CLOB  NOT NULL,
                                  beta_ips varchar2(1024) ,
                                  md5 varchar2(32) ,
                                  gmt_create timestamp(6) NOT NULL,
                                  gmt_modified timestamp(6) NOT NULL,
                                  src_user CLOB ,
                                  src_ip varchar2(20) ,
                                  tenant_id varchar2(128) DEFAULT 'PUBLIC',
                                  encrypted_data_key CLOB  NOT NULL
)
;
COMMENT ON COLUMN config_info_beta.id IS 'id';
COMMENT ON COLUMN config_info_beta.data_id IS 'data_id';
COMMENT ON COLUMN config_info_beta.group_id IS 'group_id';
COMMENT ON COLUMN config_info_beta.app_name IS 'app_name';
COMMENT ON COLUMN config_info_beta.content IS 'content';
COMMENT ON COLUMN config_info_beta.beta_ips IS 'betaIps';
COMMENT ON COLUMN config_info_beta.md5 IS 'md5';
COMMENT ON COLUMN config_info_beta.gmt_create IS '创建时间';
COMMENT ON COLUMN config_info_beta.gmt_modified IS '修改时间';
COMMENT ON COLUMN config_info_beta.src_user IS 'source user';
COMMENT ON COLUMN config_info_beta.src_ip IS 'source ip';
COMMENT ON COLUMN config_info_beta.tenant_id IS '租户字段';
COMMENT ON COLUMN config_info_beta.encrypted_data_key IS '秘钥';
COMMENT ON TABLE config_info_beta IS 'config_info_beta';


BEGIN
EXECUTE IMMEDIATE 'DROP SEQUENCE config_info_beta_id_seq';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -2289 THEN
         RAISE;
END IF;
END;
create sequence config_info_beta_id_seq
    minvalue 1
    increment by 1
    start with 1;


create or replace trigger config_info_beta_id_inc
before insert on config_info_beta for each row
begin
select config_info_beta_id_seq.nextval into:new.id from dual;
end;
-- ----------------------------
-- Records of config_info_beta
-- ----------------------------
BEGIN;
COMMIT;

-- ----------------------------
-- Table structure for config_info_tag
-- ----------------------------
BEGIN
EXECUTE IMMEDIATE 'DROP TABLE config_info_tag';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -942 THEN
         RAISE;
END IF;
END;
CREATE TABLE config_info_tag (
                                 id int NOT NULL,
                                 data_id varchar2(255)  NOT NULL,
                                 group_id varchar2(128)  NOT NULL,
                                 tenant_id varchar2(128) DEFAULT 'PUBLIC',
                                 tag_id varchar2(128)  NOT NULL,
                                 app_name varchar2(128) ,
                                 content CLOB  NOT NULL,
                                 md5 varchar2(32) ,
                                 gmt_create timestamp(6) NOT NULL,
                                 gmt_modified timestamp(6) NOT NULL,
                                 src_user CLOB ,
                                 src_ip varchar2(20)
)
;
COMMENT ON COLUMN config_info_tag.id IS 'id';
COMMENT ON COLUMN config_info_tag.data_id IS 'data_id';
COMMENT ON COLUMN config_info_tag.group_id IS 'group_id';
COMMENT ON COLUMN config_info_tag.tenant_id IS 'tenant_id';
COMMENT ON COLUMN config_info_tag.tag_id IS 'tag_id';
COMMENT ON COLUMN config_info_tag.app_name IS 'app_name';
COMMENT ON COLUMN config_info_tag.content IS 'content';
COMMENT ON COLUMN config_info_tag.md5 IS 'md5';
COMMENT ON COLUMN config_info_tag.gmt_create IS '创建时间';
COMMENT ON COLUMN config_info_tag.gmt_modified IS '修改时间';
COMMENT ON COLUMN config_info_tag.src_user IS 'source user';
COMMENT ON COLUMN config_info_tag.src_ip IS 'source ip';
COMMENT ON TABLE config_info_tag IS 'config_info_tag';


BEGIN
EXECUTE IMMEDIATE 'DROP SEQUENCE config_info_tag_id_seq';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -2289 THEN
         RAISE;
END IF;
END;
create sequence config_info_tag_id_seq
    minvalue 1
    increment by 1
    start with 1;

create or replace trigger config_info_tag_id_inc
before insert on config_info_tag for each row
begin
select config_info_tag_id_seq.nextval into:new.id from dual;
end;
-- ----------------------------
-- Records of config_info_tag
-- ----------------------------
BEGIN;
COMMIT;

-- ----------------------------
-- Table structure for config_tags_relation
-- ----------------------------
BEGIN
EXECUTE IMMEDIATE 'DROP TABLE config_tags_relation';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -942 THEN
         RAISE;
END IF;
END;
CREATE TABLE config_tags_relation (
                                      id NUMBER(20) NOT NULL,
                                      tag_name VARCHAR2(128) NOT NULL,
                                      tag_type VARCHAR2(64) DEFAULT NULL,
                                      data_id VARCHAR2(255) NOT NULL,
                                      group_id VARCHAR2(128) NOT NULL,
                                      tenant_id VARCHAR2(128) DEFAULT '',
                                      nid NUMBER(20) PRIMARY KEY
);

CREATE UNIQUE INDEX uk_configtagrelation_configidtag ON config_tags_relation (id, tag_name, tag_type);
CREATE INDEX idx_tenant_id_relation ON config_tags_relation (tenant_id);

COMMENT ON TABLE config_tags_relation IS 'config_tag_relation';
COMMENT ON COLUMN config_tags_relation.id IS 'id';
COMMENT ON COLUMN config_tags_relation.tag_name IS 'tag_name';
COMMENT ON COLUMN config_tags_relation.tag_type IS 'tag_type';
COMMENT ON COLUMN config_tags_relation.data_id IS 'data_id';
COMMENT ON COLUMN config_tags_relation.group_id IS 'group_id';
COMMENT ON COLUMN config_tags_relation.tenant_id IS 'tenant_id';
COMMENT ON COLUMN config_tags_relation.nid IS 'nid, 自增长标识';

CREATE SEQUENCE config_tags_relation_seq START WITH 1 INCREMENT BY 1 NOCACHE;

CREATE OR REPLACE TRIGGER config_tags_relation_trg
BEFORE INSERT ON config_tags_relation
FOR EACH ROW
BEGIN
    :new.nid := config_tags_relation_seq.NEXTVAL;
END;
-- ----------------------------
-- Records of config_tags_relation
-- ----------------------------
BEGIN;
COMMIT;

-- ----------------------------
-- Table structure for group_capacity
-- ----------------------------
BEGIN
EXECUTE IMMEDIATE 'DROP TABLE group_capacity';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -942 THEN
         RAISE;
END IF;
END;
CREATE TABLE group_capacity (
                                id NUMBER(20) PRIMARY KEY,
                                group_id VARCHAR2(128) DEFAULT '' NOT NULL,
                                quota NUMBER(10) DEFAULT 0 NOT NULL,
                                usage NUMBER(10) DEFAULT 0 NOT NULL,
                                max_size NUMBER(10) DEFAULT 0 NOT NULL,
                                max_aggr_count NUMBER(10) DEFAULT 0 NOT NULL,
                                max_aggr_size NUMBER(10) DEFAULT 0 NOT NULL,
                                max_history_count NUMBER(10) DEFAULT 0 NOT NULL,
                                gmt_create TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                                gmt_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE UNIQUE INDEX uk_group_id_capacity ON group_capacity (group_id);

COMMENT ON TABLE group_capacity IS '集群、各Group容量信息表';
COMMENT ON COLUMN group_capacity.id IS '主键ID';
COMMENT ON COLUMN group_capacity.group_id IS 'Group ID，空字符表示整个集群';
COMMENT ON COLUMN group_capacity.quota IS '配额，0表示使用默认值';
COMMENT ON COLUMN group_capacity.usage IS '使用量';
COMMENT ON COLUMN group_capacity.max_size IS '单个配置大小上限，单位为字节，0表示使用默认值';
COMMENT ON COLUMN group_capacity.max_aggr_count IS '聚合子配置最大个数，，0表示使用默认值';
COMMENT ON COLUMN group_capacity.max_aggr_size IS '单个聚合数据的子配置大小上限，单位为字节，0表示使用默认值';
COMMENT ON COLUMN group_capacity.max_history_count IS '最大变更历史数量';
COMMENT ON COLUMN group_capacity.gmt_create IS '创建时间';
COMMENT ON COLUMN group_capacity.gmt_modified IS '修改时间';

CREATE SEQUENCE group_capacity_seq START WITH 1 INCREMENT BY 1 NOCACHE;

CREATE OR REPLACE TRIGGER group_capacity_trg
BEFORE INSERT ON group_capacity
FOR EACH ROW
BEGIN
    :new.id := group_capacity_seq.NEXTVAL;
END;
-- ----------------------------
-- Records of group_capacity
-- ----------------------------
BEGIN;
COMMIT;

-- ----------------------------
-- Table structure for his_config_info
-- ----------------------------
BEGIN
EXECUTE IMMEDIATE 'DROP TABLE his_config_info';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -942 THEN
         RAISE;
END IF;
END;
CREATE TABLE his_config_info (
                                 id NUMBER(20) NOT NULL,
                                 nid NUMBER(20) PRIMARY KEY,
                                 data_id VARCHAR2(255) NOT NULL,
                                 group_id VARCHAR2(128) NOT NULL,
                                 app_name VARCHAR2(128) DEFAULT NULL,
                                 content CLOB NOT NULL,
                                 md5 VARCHAR2(32) DEFAULT NULL,
                                 gmt_create TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                                 gmt_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                                 src_user CLOB,
                                 src_ip VARCHAR2(50) DEFAULT NULL,
                                 op_type CHAR(10) DEFAULT NULL,
                                 tenant_id VARCHAR2(128) DEFAULT '',
                                 encrypted_data_key VARCHAR2(1024) DEFAULT '' NOT NULL,
                                 publish_type VARCHAR2(50) DEFAULT 'formal',
                                 gray_name VARCHAR2(128) DEFAULT NULL,
                                 ext_info CLOB DEFAULT NULL
);

CREATE INDEX idx_gmt_create_info ON his_config_info (gmt_create);
CREATE INDEX idx_gmt_modified_info ON his_config_info (gmt_modified);
CREATE INDEX idx_did_info ON his_config_info (data_id);

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
COMMENT ON COLUMN his_config_info.gray_name IS 'gray_name';
COMMENT ON COLUMN his_config_info.ext_info IS 'ext info';

CREATE SEQUENCE his_config_info_seq START WITH 1 INCREMENT BY 1 NOCACHE;

CREATE OR REPLACE TRIGGER his_config_info_trg
BEFORE INSERT ON his_config_info
FOR EACH ROW
BEGIN
    :new.nid := his_config_info_seq.NEXTVAL;
END;
-- ----------------------------
-- Table structure for permissions
-- ----------------------------
BEGIN
EXECUTE IMMEDIATE 'DROP TABLE permissions';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -942 THEN
         RAISE;
END IF;
END;
CREATE TABLE permissions (
                             role VARCHAR2(50) NOT NULL,
                             resource VARCHAR2(128) NOT NULL,
                             action VARCHAR2(8) NOT NULL
);

CREATE UNIQUE INDEX uk_role_permission_perm ON permissions (role, resource, action);

COMMENT ON TABLE permissions IS '权限表';
COMMENT ON COLUMN permissions.role IS 'role';
COMMENT ON COLUMN permissions.resource IS 'resource';
COMMENT ON COLUMN permissions.action IS 'action';

-- ----------------------------
-- Records of permissions
-- ----------------------------
BEGIN;
COMMIT;

-- ----------------------------
-- Table structure for roles
-- ----------------------------
BEGIN
EXECUTE IMMEDIATE 'DROP TABLE roles';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -942 THEN
         RAISE;
END IF;
END;
CREATE TABLE roles (
                       username VARCHAR2(50) NOT NULL,
                       role VARCHAR2(50) NOT NULL
);

CREATE UNIQUE INDEX idx_user_role_roles ON roles (username, role);

COMMENT ON TABLE roles IS '角色表';
COMMENT ON COLUMN roles.username IS 'username';
COMMENT ON COLUMN roles.role IS 'role';

-- ----------------------------
-- Records of roles
-- ----------------------------
BEGIN;
INSERT INTO roles VALUES ('nacos', 'ROLE_ADMIN');
COMMIT;

-- ----------------------------
-- Table structure for tenant_capacity
-- ----------------------------
BEGIN
EXECUTE IMMEDIATE 'DROP TABLE tenant_capacity';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -942 THEN
         RAISE;
END IF;
END;
CREATE TABLE tenant_capacity (
                                 id NUMBER(20) PRIMARY KEY,
                                 tenant_id VARCHAR2(128) DEFAULT '' NOT NULL,
                                 quota NUMBER(10) DEFAULT 0 NOT NULL,
                                 usage NUMBER(10) DEFAULT 0 NOT NULL,
                                 max_size NUMBER(10) DEFAULT 0 NOT NULL,
                                 max_aggr_count NUMBER(10) DEFAULT 0 NOT NULL,
                                 max_aggr_size NUMBER(10) DEFAULT 0 NOT NULL,
                                 max_history_count NUMBER(10) DEFAULT 0 NOT NULL,
                                 gmt_create TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                                 gmt_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE UNIQUE INDEX uk_tenant_id_capacity ON tenant_capacity (tenant_id);

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

CREATE SEQUENCE tenant_capacity_seq START WITH 1 INCREMENT BY 1 NOCACHE;

CREATE OR REPLACE TRIGGER tenant_capacity_trg
BEFORE INSERT ON tenant_capacity
FOR EACH ROW
BEGIN
    :new.id := tenant_capacity_seq.NEXTVAL;
END;
-- ----------------------------
-- Records of tenant_capacity
-- ----------------------------
BEGIN;
COMMIT;

-- ----------------------------
-- Table structure for tenant_info
-- ----------------------------
BEGIN
EXECUTE IMMEDIATE 'DROP TABLE tenant_info';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -942 THEN
         RAISE;
END IF;
END;
CREATE TABLE tenant_info (
                             id NUMBER(20) PRIMARY KEY,
                             kp VARCHAR2(128) NOT NULL,
                             tenant_id VARCHAR2(128) DEFAULT '',
                             tenant_name VARCHAR2(128) DEFAULT '',
                             tenant_desc VARCHAR2(256) DEFAULT NULL,
                             create_source VARCHAR2(32) DEFAULT NULL,
                             gmt_create NUMBER(20) NOT NULL,
                             gmt_modified NUMBER(20) NOT NULL
);

CREATE UNIQUE INDEX uk_tenant_info_kptenantid ON tenant_info (kp, tenant_id);
CREATE INDEX idx_tenant_id_info ON tenant_info (tenant_id);

COMMENT ON TABLE tenant_info IS 'tenant_info';
COMMENT ON COLUMN tenant_info.id IS 'id';
COMMENT ON COLUMN tenant_info.kp IS 'kp';
COMMENT ON COLUMN tenant_info.tenant_id IS 'tenant_id';
COMMENT ON COLUMN tenant_info.tenant_name IS 'tenant_name';
COMMENT ON COLUMN tenant_info.tenant_desc IS 'tenant_desc';
COMMENT ON COLUMN tenant_info.create_source IS 'create_source';
COMMENT ON COLUMN tenant_info.gmt_create IS '创建时间';
COMMENT ON COLUMN tenant_info.gmt_modified IS '修改时间';

CREATE SEQUENCE tenant_info_seq START WITH 1 INCREMENT BY 1 NOCACHE;

CREATE OR REPLACE TRIGGER tenant_info_trg
BEFORE INSERT ON tenant_info
FOR EACH ROW
BEGIN
    :new.id := tenant_info_seq.NEXTVAL;
END;
-- ----------------------------
-- Records of tenant_info
-- ----------------------------
BEGIN;
COMMIT;

-- ----------------------------
-- Table structure for users
-- ----------------------------
BEGIN
EXECUTE IMMEDIATE 'DROP TABLE users';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -942 THEN
         RAISE;
END IF;
END;
CREATE TABLE users (
                       username VARCHAR2(50) PRIMARY KEY,
                       password VARCHAR2(500) NOT NULL,
                       enabled NUMBER(1) NOT NULL
);

COMMENT ON TABLE users IS '用户表';
COMMENT ON COLUMN users.username IS 'username';
COMMENT ON COLUMN users.password IS 'password';
COMMENT ON COLUMN users.enabled IS 'enabled';

-- ----------------------------
-- Records of users
-- ----------------------------
BEGIN;
INSERT INTO users VALUES ('nacos', '$2a$10$EuWPZHzz32dJN7jexM34MOeYirDdFAZm2kuWj7VEOJhhZkDrxfvUu', 1);
COMMIT;

-- ----------------------------
-- Indexes structure for table config_info
-- ----------------------------
CREATE UNIQUE INDEX uk_configinfo_datagrouptenant ON config_info (data_id,group_id,tenant_id);

-- ----------------------------
-- Primary Key structure for table config_info
-- ----------------------------
ALTER TABLE config_info ADD CONSTRAINT config_info_pkey PRIMARY KEY (id);

-- ----------------------------
-- Indexes structure for table config_info_aggr
-- ----------------------------
CREATE UNIQUE INDEX uk_configinfoaggr_datagrouptenantdatum ON config_info_aggr (data_id,group_id,tenant_id,datum_id);

-- ----------------------------
-- Primary Key structure for table config_info_aggr
-- ----------------------------
ALTER TABLE config_info_aggr ADD CONSTRAINT config_info_aggr_pkey PRIMARY KEY (id);

-- ----------------------------
-- Indexes structure for table config_info_beta
-- ----------------------------
CREATE UNIQUE INDEX uk_configinfobeta_datagrouptenant ON config_info_beta (data_id,group_id,tenant_id);

-- ----------------------------
-- Primary Key structure for table config_info_beta
-- ----------------------------
ALTER TABLE config_info_beta ADD CONSTRAINT config_info_beta_pkey PRIMARY KEY (id);

-- ----------------------------
-- Indexes structure for table config_info_tag
-- ----------------------------
CREATE UNIQUE INDEX uk_configinfotag_datagrouptenanttag ON config_info_tag (data_id,group_id,tenant_id,tag_id);

-- ----------------------------
-- Primary Key structure for table config_info_tag
-- ----------------------------
ALTER TABLE config_info_tag ADD CONSTRAINT config_info_tag_pkey PRIMARY KEY (id);

-- ----------------------------
-- Indexes structure for table config_tags_relation
-- ----------------------------
CREATE INDEX idx_tenant_id ON config_tags_relation (
  tenant_id
);
CREATE UNIQUE INDEX uk_configtagrelation_configidtag ON config_tags_relation (
  id,
  tag_name,
  tag_type
);

-- ----------------------------
-- Primary Key structure for table config_tags_relation
-- ----------------------------
ALTER TABLE config_tags_relation ADD CONSTRAINT config_tags_relation_pkey PRIMARY KEY (nid);

-- ----------------------------
-- Indexes structure for table group_capacity
-- ----------------------------
CREATE UNIQUE INDEX uk_group_id ON group_capacity (
  group_id
);

-- ----------------------------
-- Primary Key structure for table group_capacity
-- ----------------------------
ALTER TABLE group_capacity ADD CONSTRAINT group_capacity_pkey PRIMARY KEY (id);

-- ----------------------------
-- Indexes structure for table his_config_info
-- ----------------------------
CREATE INDEX idx_did ON his_config_info (
  data_id
);
CREATE INDEX idx_gmt_create ON his_config_info (
  gmt_create
);
CREATE INDEX idx_gmt_modified ON his_config_info (
  gmt_modified
);

-- ----------------------------
-- Primary Key structure for table his_config_info
-- ----------------------------
ALTER TABLE his_config_info ADD CONSTRAINT his_config_info_pkey PRIMARY KEY (nid);

-- ----------------------------
-- Indexes structure for table permissions
-- ----------------------------
CREATE UNIQUE INDEX uk_role_permission ON permissions (
  "ROLE",
  "RESOURCE",
  "ACTION"
);

-- ----------------------------
-- Indexes structure for table roles
-- ----------------------------
CREATE UNIQUE INDEX uk_username_role ON roles (
  "USERNAME",
  "ROLE"
);

-- ----------------------------
-- Indexes structure for table tenant_capacity
-- ----------------------------
CREATE UNIQUE INDEX uk_tenant_id ON tenant_capacity (
  tenant_id
);

-- ----------------------------
-- Primary Key structure for table tenant_capacity
-- ----------------------------
ALTER TABLE tenant_capacity ADD CONSTRAINT tenant_capacity_pkey PRIMARY KEY (id);

-- ----------------------------
-- Indexes structure for table tenant_info
-- ----------------------------
CREATE UNIQUE INDEX uk_tenant_info_kptenantid ON tenant_info (
  kp,
  tenant_id
);
