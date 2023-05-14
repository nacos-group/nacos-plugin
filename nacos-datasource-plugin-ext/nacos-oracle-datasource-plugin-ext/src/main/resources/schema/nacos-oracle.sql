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
                             id int NOT NULL,
                             data_id varchar2(255)  NOT NULL,
                             group_id varchar2(255) ,
                             content CLOB  NOT NULL,
                             md5 varchar2(32) ,
                             gmt_create timestamp(6) NOT NULL,
                             gmt_modified timestamp(6) NOT NULL,
                             src_user CLOB ,
                             src_ip varchar2(20) ,
                             app_name varchar2(128) ,
                             tenant_id varchar2(128) DEFAULT 'PUBLIC',
                             c_desc varchar2(256) ,
                             c_use varchar2(64) ,
                             effect varchar2(64) ,
                             type varchar2(64) ,
                             c_schema CLOB ,
                             encrypted_data_key CLOB  DEFAULT ''
)
;

COMMENT ON COLUMN config_info.id IS 'id';
COMMENT ON COLUMN config_info.data_id IS 'data_id';
COMMENT ON COLUMN config_info.content IS 'content';
COMMENT ON COLUMN config_info.md5 IS 'md5';
COMMENT ON COLUMN config_info.gmt_create IS '创建时间';
COMMENT ON COLUMN config_info.gmt_modified IS '修改时间';
COMMENT ON COLUMN config_info.src_user IS 'source user';
COMMENT ON COLUMN config_info.src_ip IS 'source ip';
COMMENT ON COLUMN config_info.tenant_id IS '租户字段';
COMMENT ON COLUMN config_info.encrypted_data_key IS '秘钥';
COMMENT ON TABLE config_info IS 'config_info';


BEGIN
EXECUTE IMMEDIATE 'DROP SEQUENCE config_info_id_seq';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -2289 THEN
         RAISE;
END IF;
END;
create sequence config_info_id_seq
    minvalue 1
    increment by 1
    start with 1;

create or replace trigger config_info_id_inc
before insert on config_info for each row
begin
select config_info_id_seq.nextval into:new.id from dual;
end;
-- ----------------------------
-- Table structure for config_info_aggr
-- ----------------------------
BEGIN
EXECUTE IMMEDIATE 'DROP TABLE config_info_aggr';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -942 THEN
         RAISE;
END IF;
END;
CREATE TABLE config_info_aggr (
                                  id int NOT NULL,
                                  data_id varchar2(255)  NOT NULL,
                                  group_id varchar2(255)  NOT NULL,
                                  datum_id varchar2(255)  NOT NULL,
                                  content CLOB  NOT NULL,
                                  gmt_modified timestamp(6) NOT NULL,
                                  app_name varchar2(128) ,
                                  tenant_id varchar2(128) DEFAULT 'PUBLIC'
)
;
COMMENT ON COLUMN config_info_aggr.id IS 'id';
COMMENT ON COLUMN config_info_aggr.data_id IS 'data_id';
COMMENT ON COLUMN config_info_aggr.group_id IS 'group_id';
COMMENT ON COLUMN config_info_aggr.datum_id IS 'datum_id';
COMMENT ON COLUMN config_info_aggr.content IS '内容';
COMMENT ON COLUMN config_info_aggr.gmt_modified IS '修改时间';
COMMENT ON COLUMN config_info_aggr.tenant_id IS '租户字段';
COMMENT ON TABLE config_info_aggr IS '增加租户字段';


BEGIN
EXECUTE IMMEDIATE 'DROP SEQUENCE config_info_aggr_id_seq';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -2289 THEN
         RAISE;
END IF;
END;
create sequence config_info_aggr_id_seq
    minvalue 1
    increment by 1
    start with 1;

create or replace trigger config_info_aggr_id_inc
before insert on config_info_aggr for each row
begin
select config_info_aggr_id_seq.nextval into:new.id from dual;
end;
-- ----------------------------
-- Records of config_info_aggr
-- ----------------------------
BEGIN;
COMMIT;

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
                                      id int NOT NULL,
                                      tag_name varchar2(128)  NOT NULL,
                                      tag_type varchar2(64) ,
                                      data_id varchar2(255)  NOT NULL,
                                      group_id varchar2(128)  NOT NULL,
                                      tenant_id varchar2(128) DEFAULT 'PUBLIC',
                                      nid int NOT NULL
)
;
COMMENT ON COLUMN config_tags_relation.id IS 'id';
COMMENT ON COLUMN config_tags_relation.tag_name IS 'tag_name';
COMMENT ON COLUMN config_tags_relation.tag_type IS 'tag_type';
COMMENT ON COLUMN config_tags_relation.data_id IS 'data_id';
COMMENT ON COLUMN config_tags_relation.group_id IS 'group_id';
COMMENT ON COLUMN config_tags_relation.tenant_id IS 'tenant_id';
COMMENT ON TABLE config_tags_relation IS 'config_tag_relation';


BEGIN
EXECUTE IMMEDIATE 'DROP SEQUENCE config_tags_relation_id_seq';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -2289 THEN
         RAISE;
END IF;
END;
create sequence config_tags_relation_id_seq
    minvalue 1
    increment by 1
    start with 1;

create or replace trigger config_tags_relation_id_inc
before insert on config_tags_relation for each row
begin
select config_tags_relation_id_seq.nextval into:new.id from dual;
end;
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
                                id int NOT NULL,
                                group_id varchar2(128)  NOT NULL,
                                quota int NOT NULL,
                                usage int NOT NULL,
                                max_size int NOT NULL,
                                max_aggr_count int NOT NULL,
                                max_aggr_size int NOT NULL,
                                max_history_count int NOT NULL,
                                gmt_create timestamp(6) NOT NULL,
                                gmt_modified timestamp(6) NOT NULL
)
;
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
COMMENT ON TABLE group_capacity IS '集群、各Group容量信息表';


BEGIN
EXECUTE IMMEDIATE 'DROP SEQUENCE group_capacity_id_seq';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -2289 THEN
         RAISE;
END IF;
END;
create sequence group_capacity_id_seq
    minvalue 1
    increment by 1
    start with 1;

create or replace trigger group_capacity_id_inc
before insert on group_capacity for each row
begin
select group_capacity_id_seq.nextval into:new.id from dual;
end;
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
                                 id int NOT NULL,
                                 nid int NOT NULL,
                                 data_id varchar2(255)  NOT NULL,
                                 group_id varchar2(128)  NOT NULL,
                                 app_name varchar2(128) ,
                                 content CLOB  NOT NULL,
                                 md5 varchar2(32) ,
                                 gmt_create timestamp(6) DEFAULT CURRENT_TIMESTAMP,
                                 gmt_modified timestamp(6) NOT NULL,
                                 src_user CLOB ,
                                 src_ip varchar2(20) ,
                                 op_type char(10) ,
                                 tenant_id varchar2(128) DEFAULT 'PUBLIC',
                                 encrypted_data_key CLOB  DEFAULT ''
)
;
COMMENT ON COLUMN his_config_info.app_name IS 'app_name';
COMMENT ON COLUMN his_config_info.tenant_id IS '租户字段';
COMMENT ON COLUMN his_config_info.encrypted_data_key IS '秘钥';
COMMENT ON TABLE his_config_info IS '多租户改造';


BEGIN
EXECUTE IMMEDIATE 'DROP SEQUENCE his_config_info_nid_seq';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -2289 THEN
         RAISE;
END IF;
END;
create sequence his_config_info_nid_seq
    minvalue 1
    increment by 1
    start with 1;

create or replace trigger his_config_info_nid_inc
before insert on his_config_info for each row
begin
select his_config_info_nid_seq.nextval into:new.nid from dual;
end;
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
                             "ROLE" varchar2(50)  NOT NULL,
                             "RESOURCE" varchar2(512)  NOT NULL,
                             "ACTION" varchar2(8)  NOT NULL
)
;

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
                       "USERNAME" varchar2(50)  NOT NULL,
                       "ROLE" varchar2(50)  NOT NULL
)
;

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
                                 id int NOT NULL,
                                 tenant_id varchar2(128)  NOT NULL,
                                 quota int NOT NULL,
                                 usage int NOT NULL,
                                 max_size int NOT NULL,
                                 max_aggr_count int NOT NULL,
                                 max_aggr_size int NOT NULL,
                                 max_history_count int NOT NULL,
                                 gmt_create timestamp(6) NOT NULL,
                                 gmt_modified timestamp(6) NOT NULL
)
;
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
COMMENT ON TABLE tenant_capacity IS '租户容量信息表';


BEGIN
EXECUTE IMMEDIATE 'DROP SEQUENCE tenant_capacity_id_seq';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -2289 THEN
         RAISE;
END IF;
END;
create sequence tenant_capacity_id_seq
    minvalue 1
    increment by 1
    start with 1;


create or replace trigger tenant_capacity_id_inc
before insert on tenant_capacity for each row
begin
select tenant_capacity_id_seq.nextval into:new.id from dual;
end;
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
                             id int NOT NULL,
                             kp varchar2(128)  NOT NULL,
                             tenant_id varchar2(128) DEFAULT 'PUBLIC',
                             tenant_name varchar2(128) ,
                             tenant_desc varchar2(256) ,
                             create_source varchar2(32) ,
                             gmt_create int NOT NULL,
                             gmt_modified int NOT NULL
)
;
COMMENT ON COLUMN tenant_info.id IS 'id';
COMMENT ON COLUMN tenant_info.kp IS 'kp';
COMMENT ON COLUMN tenant_info.tenant_id IS 'tenant_id';
COMMENT ON COLUMN tenant_info.tenant_name IS 'tenant_name';
COMMENT ON COLUMN tenant_info.tenant_desc IS 'tenant_desc';
COMMENT ON COLUMN tenant_info.create_source IS 'create_source';
COMMENT ON COLUMN tenant_info.gmt_create IS '创建时间';
COMMENT ON COLUMN tenant_info.gmt_modified IS '修改时间';
COMMENT ON TABLE tenant_info IS 'tenant_info';


BEGIN
EXECUTE IMMEDIATE 'DROP SEQUENCE tenant_info_id_seq';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -2289 THEN
         RAISE;
END IF;
END;
create sequence tenant_info_id_seq
    minvalue 1
    increment by 1
    start with 1;

create or replace trigger tenant_info_id_inc
before insert on tenant_info for each row
begin
select tenant_info_id_seq.nextval into:new.id from dual;
end;
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
                       username varchar2(50)  NOT NULL,
                       password varchar2(500)  NOT NULL,
                       enabled NUMBER(1) NOT NULL
)
;

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
