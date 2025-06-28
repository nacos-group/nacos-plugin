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

-- Table: config_info
CREATE TABLE config_info (
                             id BIGINT IDENTITY(1,1) NOT NULL,
                             data_id NVARCHAR(255) NOT NULL,
                             group_id NVARCHAR(128) NULL,
                             content NVARCHAR(MAX) NOT NULL,
                             md5 NVARCHAR(32) NULL,
                             gmt_create DATETIME2 NOT NULL DEFAULT CURRENT_TIMESTAMP,
                             gmt_modified DATETIME2 NOT NULL DEFAULT CURRENT_TIMESTAMP,
                             src_user NVARCHAR(MAX) NULL,
                             src_ip NVARCHAR(50) NULL,
                             app_name NVARCHAR(128) NULL,
                             tenant_id NVARCHAR(128) DEFAULT N'',
                             c_desc NVARCHAR(256) NULL,
                             c_use NVARCHAR(64) NULL,
                             effect NVARCHAR(64) NULL,
                             type NVARCHAR(64) NULL,
                             c_schema NVARCHAR(MAX) NULL,
                             encrypted_data_key NVARCHAR(1024) NOT NULL DEFAULT N''
);

ALTER TABLE config_info ADD CONSTRAINT PK_config_info PRIMARY KEY (id);
CREATE UNIQUE INDEX uk_configinfo_datagrouptenant ON config_info (data_id, group_id, tenant_id);

-- Table: config_info_gray
CREATE TABLE config_info_gray (
                                  id BIGINT IDENTITY(1,1) NOT NULL,
                                  data_id NVARCHAR(255) NOT NULL,
                                  group_id NVARCHAR(128) NOT NULL,
                                  content NVARCHAR(MAX) NOT NULL,
                                  md5 NVARCHAR(32) NULL,
                                  src_user NVARCHAR(MAX) NULL,
                                  src_ip NVARCHAR(100) NULL,
                                  gmt_create DATETIME2(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                  gmt_modified DATETIME2(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                  app_name NVARCHAR(128) NULL,
                                  tenant_id NVARCHAR(128) DEFAULT N'',
                                  gray_name NVARCHAR(128) NOT NULL,
                                  gray_rule NVARCHAR(MAX) NOT NULL,
                                  encrypted_data_key NVARCHAR(256) NOT NULL DEFAULT N''
);

ALTER TABLE config_info_gray ADD CONSTRAINT PK_config_info_gray PRIMARY KEY (id);
CREATE UNIQUE INDEX uk_configinfogray_datagrouptenantgray ON config_info_gray (data_id, group_id, tenant_id, gray_name);
CREATE INDEX idx_dataid_gmt_modified_gray ON config_info_gray (data_id, gmt_modified);
CREATE INDEX idx_gmt_modified_gray ON config_info_gray (gmt_modified);


-- Table: config_info_beta
CREATE TABLE config_info_beta (
     id bigint NOT NULL IDENTITY(1,1) PRIMARY KEY,
     data_id varchar(255) NOT NULL,
     group_id varchar(128) NOT NULL,
     app_name varchar(128) NULL,
     content nvarchar(max) NOT NULL,
     beta_ips varchar(1024) NULL,
     md5 varchar(32) NULL,
     gmt_create datetime NOT NULL DEFAULT GETDATE(),
     gmt_modified datetime NOT NULL DEFAULT GETDATE(),
     src_user nvarchar(max),
     src_ip varchar(50) NULL,
     tenant_id varchar(128) DEFAULT '',
     encrypted_data_key nvarchar(max) NOT NULL,
     UNIQUE (data_id, group_id, tenant_id)
);

-- Table: config_info_tag
CREATE TABLE config_info_tag (
    id bigint NOT NULL IDENTITY(1,1) PRIMARY KEY,
    data_id varchar(255) NOT NULL,
    group_id varchar(128) NOT NULL,
    tenant_id varchar(128) DEFAULT '',
    tag_id varchar(128) NOT NULL,
    app_name varchar(128) NULL,
    content nvarchar(max) NOT NULL,
    md5 varchar(32) NULL,
    gmt_create datetime NOT NULL DEFAULT GETDATE(),
    gmt_modified datetime NOT NULL DEFAULT GETDATE(),
    src_user nvarchar(max),
    src_ip varchar(50) NULL,
    UNIQUE (data_id, group_id, tenant_id, tag_id)
);

-- Table: config_tags_relation
CREATE TABLE config_tags_relation (
                                      id BIGINT NOT NULL,
                                      tag_name NVARCHAR(128) NOT NULL,
                                      tag_type NVARCHAR(64) NULL,
                                      data_id NVARCHAR(255) NOT NULL,
                                      group_id NVARCHAR(128) NOT NULL,
                                      tenant_id NVARCHAR(128) DEFAULT N'',
                                      nid BIGINT IDENTITY(1,1) NOT NULL
);

ALTER TABLE config_tags_relation ADD CONSTRAINT PK_config_tags_relation PRIMARY KEY (nid);
CREATE UNIQUE INDEX uk_configtagrelation_configidtag ON config_tags_relation (id, tag_name, tag_type);
CREATE INDEX idx_tenant_id_relation ON config_tags_relation (tenant_id);

-- Table: group_capacity
CREATE TABLE group_capacity (
                                id BIGINT IDENTITY(1,1) NOT NULL,
                                group_id NVARCHAR(128) NOT NULL DEFAULT N'',
                                quota INT NOT NULL DEFAULT 0,
                                usage INT NOT NULL DEFAULT 0,
                                max_size INT NOT NULL DEFAULT 0,
                                max_aggr_count INT NOT NULL DEFAULT 0,
                                max_aggr_size INT NOT NULL DEFAULT 0,
                                max_history_count INT NOT NULL DEFAULT 0,
                                gmt_create DATETIME2 NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                gmt_modified DATETIME2 NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE group_capacity ADD CONSTRAINT PK_group_capacity PRIMARY KEY (id);
CREATE UNIQUE INDEX uk_group_id_capacity ON group_capacity (group_id);


-- Table: his_config_info
CREATE TABLE his_config_info (
                                 id BIGINT NOT NULL,
                                 nid BIGINT IDENTITY(1,1) NOT NULL,
                                 data_id NVARCHAR(255) NOT NULL,
                                 group_id NVARCHAR(128) NOT NULL,
                                 app_name NVARCHAR(128) NULL,
                                 content NVARCHAR(MAX) NOT NULL,
                                 md5 NVARCHAR(32) NULL,
                                 gmt_create DATETIME2 NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                 gmt_modified DATETIME2 NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                 src_user NVARCHAR(MAX) NULL,
                                 src_ip NVARCHAR(50) NULL,
                                 op_type NCHAR(10) NULL,
                                 tenant_id NVARCHAR(128) DEFAULT N'',
                                 encrypted_data_key NVARCHAR(1024) NOT NULL DEFAULT N'',
                                 publish_type NVARCHAR(50) DEFAULT N'formal',
                                 gray_name NVARCHAR(128) NULL,
                                 ext_info NVARCHAR(MAX) NULL
);

ALTER TABLE his_config_info ADD CONSTRAINT PK_his_config_info PRIMARY KEY (nid);
CREATE INDEX idx_gmt_create_info ON his_config_info (gmt_create);
CREATE INDEX idx_gmt_modified_info ON his_config_info (gmt_modified);
CREATE INDEX idx_did_info ON his_config_info (data_id);

-- Table: tenant_capacity
CREATE TABLE tenant_capacity (
                                 id BIGINT IDENTITY(1,1) NOT NULL,
                                 tenant_id NVARCHAR(128) NOT NULL DEFAULT N'',
                                 quota INT NOT NULL DEFAULT 0,
                                 usage INT NOT NULL DEFAULT 0,
                                 max_size INT NOT NULL DEFAULT 0,
                                 max_aggr_count INT NOT NULL DEFAULT 0,
                                 max_aggr_size INT NOT NULL DEFAULT 0,
                                 max_history_count INT NOT NULL DEFAULT 0,
                                 gmt_create DATETIME2 NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                 gmt_modified DATETIME2 NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE tenant_capacity ADD CONSTRAINT PK_tenant_capacity PRIMARY KEY (id);
CREATE UNIQUE INDEX uk_tenant_id_capacity ON tenant_capacity (tenant_id);


-- Table: tenant_info
CREATE TABLE tenant_info (
                             id BIGINT IDENTITY(1,1) NOT NULL,
                             kp NVARCHAR(128) NOT NULL,
                             tenant_id NVARCHAR(128) DEFAULT N'',
                             tenant_name NVARCHAR(128) DEFAULT N'',
                             tenant_desc NVARCHAR(256) NULL,
                             create_source NVARCHAR(32) NULL,
                             gmt_create BIGINT NOT NULL,
                             gmt_modified BIGINT NOT NULL
);

ALTER TABLE tenant_info ADD CONSTRAINT PK_tenant_info PRIMARY KEY (id);
CREATE UNIQUE INDEX uk_tenant_info_kptenantid ON tenant_info (kp, tenant_id);
CREATE INDEX idx_tenant_id_info ON tenant_info (tenant_id);

CREATE TABLE users (
                       username NVARCHAR(50) NOT NULL PRIMARY KEY,
                       password NVARCHAR(500) NOT NULL,
                       enabled BIT NOT NULL
);

CREATE TABLE roles (
                       username NVARCHAR(50) NOT NULL,
                       role NVARCHAR(50) NOT NULL
);
CREATE UNIQUE INDEX idx_user_role_roles ON roles (username, role);

CREATE TABLE permissions (
                             role NVARCHAR(50) NOT NULL,
                             resource NVARCHAR(128) NOT NULL,
                             action NVARCHAR(8) NOT NULL
);

CREATE UNIQUE INDEX uk_role_permission_perm ON permissions (role, resource, action);

INSERT INTO users (username, [password], [enabled]) VALUES ('nacos', '$2a$10$EuWPZHzz32dJN7jexM34MOeYirDdFAZm2kuWj7VEOJhhZkDrxfvUu', 1);

INSERT INTO roles (username, [role]) VALUES ('nacos', 'ROLE_ADMIN');

GO

-- 实现两个字段的自增
CREATE TRIGGER trg_config_tags_relation
    ON config_tags_relation
    AFTER INSERT
    AS
BEGIN
    UPDATE config_tags_relation
    SET nid = id
    WHERE id IN (SELECT id FROM inserted)
END
