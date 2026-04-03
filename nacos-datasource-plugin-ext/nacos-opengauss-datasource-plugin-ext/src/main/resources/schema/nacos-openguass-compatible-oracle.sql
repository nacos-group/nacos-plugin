/*
 * Copyright 1999-2026 Alibaba Group Holding Ltd.
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

/******************************************/
/*   表名称 = config_info                  */
/******************************************/
CREATE TABLE config_info (
                             id BIGSERIAL PRIMARY KEY,
                             data_id VARCHAR(255) NOT NULL,
                             group_id VARCHAR(128),
                             content TEXT NOT NULL,
                             md5 VARCHAR(32),
                             gmt_create TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                             gmt_modified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                             src_user TEXT,
                             src_ip VARCHAR(50),
                             app_name VARCHAR(128),
                             tenant_id VARCHAR(128) DEFAULT '',
                             c_desc VARCHAR(256),
                             c_use VARCHAR(64),
                             effect VARCHAR(64),
                             type VARCHAR(64),
                             c_schema TEXT,
                             encrypted_data_key VARCHAR(1024) NOT NULL DEFAULT '',
                             CONSTRAINT uk_configinfo_datagrouptenant UNIQUE (data_id, group_id, tenant_id)
);

/******************************************/
/*   表名称 = config_info_gray  since 2.5.0 */
/******************************************/
CREATE TABLE config_info_gray (
                                  id BIGSERIAL PRIMARY KEY,
                                  data_id VARCHAR(255) NOT NULL,
                                  group_id VARCHAR(128) NOT NULL,
                                  content TEXT NOT NULL,
                                  md5 VARCHAR(32),
                                  src_user TEXT,
                                  src_ip VARCHAR(100),
                                  gmt_create TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                  gmt_modified TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                  app_name VARCHAR(128),
                                  tenant_id VARCHAR(128) DEFAULT '',
                                  gray_name VARCHAR(128) NOT NULL,
                                  gray_rule TEXT NOT NULL,
                                  encrypted_data_key VARCHAR(256) NOT NULL DEFAULT '',
                                  CONSTRAINT uk_configinfogray_datagrouptenantgray UNIQUE (data_id, group_id, tenant_id, gray_name)
);

CREATE INDEX idx_config_info_gray_dataid_gmt_modified ON config_info_gray (data_id, gmt_modified);
CREATE INDEX idx_config_info_gray_gmt_modified ON config_info_gray (gmt_modified);

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
                                      nid BIGSERIAL PRIMARY KEY,
                                      CONSTRAINT uk_configtagrelation_configidtag UNIQUE (id, tag_name, tag_type)
);

CREATE INDEX idx_config_tags_relation_tenant_id ON config_tags_relation (tenant_id);

/******************************************/
/*   表名称 = group_capacity               */
/******************************************/
CREATE TABLE group_capacity (
                                id BIGSERIAL PRIMARY KEY,
                                group_id VARCHAR(128) NOT NULL DEFAULT '',
                                quota INT NOT NULL DEFAULT 0,
                                usage INT NOT NULL DEFAULT 0,
                                max_size INT NOT NULL DEFAULT 0,
                                max_aggr_count INT NOT NULL DEFAULT 0,
                                max_aggr_size INT NOT NULL DEFAULT 0,
                                max_history_count INT NOT NULL DEFAULT 0,
                                gmt_create TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                gmt_modified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                CONSTRAINT uk_group_capacity_group_id UNIQUE (group_id)
);

/******************************************/
/*   表名称 = his_config_info              */
/******************************************/
CREATE TABLE his_config_info (
                                 id BIGINT NOT NULL,
                                 nid BIGSERIAL PRIMARY KEY,
                                 data_id VARCHAR(255) NOT NULL,
                                 group_id VARCHAR(128) NOT NULL,
                                 app_name VARCHAR(128),
                                 content TEXT NOT NULL,
                                 md5 VARCHAR(32),
                                 gmt_create TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                 gmt_modified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                 src_user TEXT,
                                 src_ip VARCHAR(50),
                                 op_type CHAR(10),
                                 tenant_id VARCHAR(128) DEFAULT '',
                                 encrypted_data_key VARCHAR(1024) NOT NULL DEFAULT '',
                                 publish_type VARCHAR(50) DEFAULT 'formal',
                                 gray_name VARCHAR(50),
                                 ext_info TEXT
);

CREATE INDEX idx_his_config_info_gmt_create ON his_config_info (gmt_create);
CREATE INDEX idx_his_config_info_gmt_modified ON his_config_info (gmt_modified);
CREATE INDEX idx_his_config_info_data_id ON his_config_info (data_id);

/******************************************/
/*   表名称 = tenant_capacity              */
/******************************************/
CREATE TABLE tenant_capacity (
                                 id BIGSERIAL PRIMARY KEY,
                                 tenant_id VARCHAR(128) NOT NULL DEFAULT '',
                                 quota INT NOT NULL DEFAULT 0,
                                 usage INT NOT NULL DEFAULT 0,
                                 max_size INT NOT NULL DEFAULT 0,
                                 max_aggr_count INT NOT NULL DEFAULT 0,
                                 max_aggr_size INT NOT NULL DEFAULT 0,
                                 max_history_count INT NOT NULL DEFAULT 0,
                                 gmt_create TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                 gmt_modified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                 CONSTRAINT uk_tenant_capacity_tenant_id UNIQUE (tenant_id)
);

/******************************************/
/*   表名称 = tenant_info                  */
/******************************************/
CREATE TABLE tenant_info (
                             id BIGSERIAL PRIMARY KEY,
                             kp VARCHAR(128) NOT NULL,
                             tenant_id VARCHAR(128) DEFAULT '',
                             tenant_name VARCHAR(128) DEFAULT '',
                             tenant_desc VARCHAR(256),
                             create_source VARCHAR(32),
                             gmt_create BIGINT NOT NULL,
                             gmt_modified BIGINT NOT NULL,
                             CONSTRAINT uk_tenant_info_kptenantid UNIQUE (kp, tenant_id)
);

CREATE INDEX idx_tenant_info_tenant_id ON tenant_info (tenant_id);

/******************************************/
/*   表名称 = users                        */
/******************************************/
CREATE TABLE users (
                       username VARCHAR(50) PRIMARY KEY,
                       password VARCHAR(500) NOT NULL,
                       enabled BOOLEAN NOT NULL
);

/******************************************/
/*   表名称 = roles                        */
/******************************************/
CREATE TABLE roles (
                       username VARCHAR(50) NOT NULL,
                       role VARCHAR(50) NOT NULL,
                       CONSTRAINT uk_roles_user_role UNIQUE (username, role)
);

/******************************************/
/*   表名称 = permissions                  */
/******************************************/
CREATE TABLE permissions (
                             role VARCHAR(50) NOT NULL,
                             resource VARCHAR(128) NOT NULL,
                             action VARCHAR(8) NOT NULL,
                             CONSTRAINT uk_permissions_role_permission UNIQUE (role, resource, action)
);

/*******************************************/
/*   表名称 = pipeline_execution since 3.2.0*/
/*******************************************/
CREATE TABLE "pipeline_execution" (
    "execution_id"  varchar(64)  NOT NULL,
    "resource_type" varchar(32)  NOT NULL,
    "resource_name" varchar(256) NOT NULL,
    "namespace_id"  varchar(128) DEFAULT NULL,
    "version"       varchar(64)  DEFAULT NULL,
    "status"        varchar(32)  NOT NULL,
    "pipeline"      text         NOT NULL,
    "create_time"   bigint       NOT NULL,
    "update_time"   bigint       NOT NULL,
    PRIMARY KEY ("execution_id")
);

COMMENT ON TABLE "pipeline_execution" IS 'AI资源发布审核Pipeline执行记录';

COMMENT ON COLUMN "pipeline_execution"."execution_id"  IS '执行ID';
COMMENT ON COLUMN "pipeline_execution"."resource_type" IS '资源类型';
COMMENT ON COLUMN "pipeline_execution"."resource_name" IS '资源名称';
COMMENT ON COLUMN "pipeline_execution"."namespace_id"  IS '命名空间ID';
COMMENT ON COLUMN "pipeline_execution"."version"       IS '版本';
COMMENT ON COLUMN "pipeline_execution"."status"        IS '执行状态';
COMMENT ON COLUMN "pipeline_execution"."pipeline"      IS 'pipeline节点结果JSON';
COMMENT ON COLUMN "pipeline_execution"."create_time"   IS '创建时间';
COMMENT ON COLUMN "pipeline_execution"."update_time"   IS '修改时间';

/*******************************************/
/*   表名称 = ai_resource since 3.2.0*/
/*******************************************/
CREATE TABLE "ai_resource" (
    "id"            BIGSERIAL PRIMARY KEY,
    "gmt_create"    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "gmt_modified"  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "name"          varchar(256) NOT NULL,
    "type"          varchar(32) NOT NULL,
    "c_desc"        varchar(2048) DEFAULT NULL,
    "status"        varchar(32) DEFAULT NULL,
    "namespace_id"  varchar(128) NOT NULL DEFAULT '',
    "biz_tags"      varchar(1024) DEFAULT NULL,
    "ext"           text DEFAULT NULL,
    "c_from"        varchar(256) NOT NULL DEFAULT 'local',
    "version_info"  text DEFAULT NULL,
    "meta_version"  bigint NOT NULL DEFAULT 1,
    "scope"         varchar(16) NOT NULL DEFAULT 'PRIVATE',
    "owner"         varchar(128) NOT NULL DEFAULT '',
    "download_count" bigint NOT NULL DEFAULT 0,
    CONSTRAINT "uk_ai_resource_ns_name_type" UNIQUE ("namespace_id", "name", "type", "c_from")
);

COMMENT ON TABLE "ai_resource" IS 'AI资源元数据表';

COMMENT ON COLUMN "ai_resource"."id" IS 'id';
COMMENT ON COLUMN "ai_resource"."gmt_create" IS '创建时间';
COMMENT ON COLUMN "ai_resource"."gmt_modified" IS '修改时间';
COMMENT ON COLUMN "ai_resource"."name" IS '资源名称';
COMMENT ON COLUMN "ai_resource"."type" IS '资源类型';
COMMENT ON COLUMN "ai_resource"."c_desc" IS '资源描述';
COMMENT ON COLUMN "ai_resource"."status" IS '资源状态';
COMMENT ON COLUMN "ai_resource"."namespace_id" IS '命名空间ID';
COMMENT ON COLUMN "ai_resource"."biz_tags" IS '业务标签';
COMMENT ON COLUMN "ai_resource"."ext" IS '扩展信息(JSON)';
COMMENT ON COLUMN "ai_resource"."c_from" IS '来源标识(导入/同步来源)';
COMMENT ON COLUMN "ai_resource"."version_info" IS '版本信息(JSON)';
COMMENT ON COLUMN "ai_resource"."meta_version" IS '元数据版本(乐观锁)';
COMMENT ON COLUMN "ai_resource"."scope" IS '可见性: PUBLIC/PRIVATE';
COMMENT ON COLUMN "ai_resource"."owner" IS '创建者用户名';
COMMENT ON COLUMN "ai_resource"."download_count" IS '下载次数';

CREATE INDEX "idx_ai_resource_name" ON "ai_resource" ("name");
CREATE INDEX "idx_ai_resource_type" ON "ai_resource" ("type");
CREATE INDEX "idx_ai_resource_gmt_modified" ON "ai_resource" ("gmt_modified");

/*******************************************/
/*   表名称 = ai_resource_version since 3.2.0*/
/*******************************************/
CREATE TABLE "ai_resource_version" (
    "id"                    BIGSERIAL PRIMARY KEY,
    "gmt_create"            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "gmt_modified"          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "type"                  varchar(32) NOT NULL,
    "author"                varchar(128) DEFAULT NULL,
    "name"                  varchar(256) NOT NULL,
    "c_desc"                varchar(2048) DEFAULT NULL,
    "status"                varchar(32) NOT NULL,
    "version"               varchar(64) NOT NULL,
    "namespace_id"          varchar(128) NOT NULL DEFAULT '',
    "storage"               text DEFAULT NULL,
    "publish_pipeline_info" text DEFAULT NULL,
    "download_count"        bigint NOT NULL DEFAULT 0,
    CONSTRAINT "uk_ai_resource_ver_ns_name_type_ver" UNIQUE ("namespace_id", "name", "type", "version")
);

COMMENT ON TABLE "ai_resource_version" IS 'AI资源版本表';

COMMENT ON COLUMN "ai_resource_version"."id" IS 'id';
COMMENT ON COLUMN "ai_resource_version"."gmt_create" IS '创建时间';
COMMENT ON COLUMN "ai_resource_version"."gmt_modified" IS '修改时间';
COMMENT ON COLUMN "ai_resource_version"."type" IS '资源类型';
COMMENT ON COLUMN "ai_resource_version"."author" IS '作者';
COMMENT ON COLUMN "ai_resource_version"."name" IS '资源名称';
COMMENT ON COLUMN "ai_resource_version"."c_desc" IS '版本描述';
COMMENT ON COLUMN "ai_resource_version"."status" IS '版本状态';
COMMENT ON COLUMN "ai_resource_version"."version" IS '版本号';
COMMENT ON COLUMN "ai_resource_version"."namespace_id" IS '命名空间ID';
COMMENT ON COLUMN "ai_resource_version"."storage" IS '存储信息(JSON)';
COMMENT ON COLUMN "ai_resource_version"."publish_pipeline_info" IS '发布流水线信息(JSON)';
COMMENT ON COLUMN "ai_resource_version"."download_count" IS '下载次数';

CREATE INDEX "idx_ai_resource_ver_name" ON "ai_resource_version" ("name");
CREATE INDEX "idx_ai_resource_ver_status" ON "ai_resource_version" ("status");
CREATE INDEX "idx_ai_resource_ver_gmt_modified" ON "ai_resource_version" ("gmt_modified");