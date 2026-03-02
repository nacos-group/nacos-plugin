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