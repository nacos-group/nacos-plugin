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
-- PostgreSQL Database Schema for Nacos 3.x
-- Compatible with Nacos 3.1.1
-- =====================================================

-- ----------------------------
-- Table structure for config_info
-- ----------------------------
DROP TABLE IF EXISTS "config_info";
CREATE TABLE "config_info" (
  "id" bigserial NOT NULL,
  "data_id" varchar(255) NOT NULL,
  "group_id" varchar(255),
  "content" text NOT NULL,
  "md5" varchar(32),
  "gmt_create" timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "gmt_modified" timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "src_user" text,
  "src_ip" varchar(50),
  "app_name" varchar(128),
  "tenant_id" varchar(128) DEFAULT '',
  "c_desc" varchar(256),
  "c_use" varchar(64),
  "effect" varchar(64),
  "type" varchar(64),
  "c_schema" text,
  "encrypted_data_key" text NOT NULL DEFAULT ''
);

COMMENT ON COLUMN "config_info"."id" IS 'id';
COMMENT ON COLUMN "config_info"."data_id" IS 'data_id';
COMMENT ON COLUMN "config_info"."content" IS 'content';
COMMENT ON COLUMN "config_info"."md5" IS 'md5';
COMMENT ON COLUMN "config_info"."gmt_create" IS 'create time';
COMMENT ON COLUMN "config_info"."gmt_modified" IS 'modified time';
COMMENT ON COLUMN "config_info"."src_user" IS 'source user';
COMMENT ON COLUMN "config_info"."src_ip" IS 'source ip';
COMMENT ON COLUMN "config_info"."tenant_id" IS 'tenant id';
COMMENT ON COLUMN "config_info"."encrypted_data_key" IS 'encrypted data key';
COMMENT ON TABLE "config_info" IS 'config_info';

-- ----------------------------
-- Table structure for config_info_gray (since Nacos 2.5.0)
-- ----------------------------
DROP TABLE IF EXISTS "config_info_gray";
CREATE TABLE "config_info_gray" (
  "id" bigserial NOT NULL,
  "data_id" varchar(255) NOT NULL,
  "group_id" varchar(128) NOT NULL,
  "content" text NOT NULL,
  "md5" varchar(32),
  "src_user" text,
  "src_ip" varchar(100),
  "gmt_create" timestamp(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "gmt_modified" timestamp(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "app_name" varchar(128),
  "tenant_id" varchar(128) DEFAULT '',
  "gray_name" varchar(128) NOT NULL,
  "gray_rule" text NOT NULL,
  "encrypted_data_key" varchar(256) NOT NULL DEFAULT ''
);

COMMENT ON COLUMN "config_info_gray"."id" IS 'id';
COMMENT ON COLUMN "config_info_gray"."data_id" IS 'data_id';
COMMENT ON COLUMN "config_info_gray"."group_id" IS 'group_id';
COMMENT ON COLUMN "config_info_gray"."content" IS 'content';
COMMENT ON COLUMN "config_info_gray"."md5" IS 'md5';
COMMENT ON COLUMN "config_info_gray"."src_user" IS 'src_user';
COMMENT ON COLUMN "config_info_gray"."src_ip" IS 'src_ip';
COMMENT ON COLUMN "config_info_gray"."gmt_create" IS 'gmt_create';
COMMENT ON COLUMN "config_info_gray"."gmt_modified" IS 'gmt_modified';
COMMENT ON COLUMN "config_info_gray"."app_name" IS 'app_name';
COMMENT ON COLUMN "config_info_gray"."tenant_id" IS 'tenant_id';
COMMENT ON COLUMN "config_info_gray"."gray_name" IS 'gray_name';
COMMENT ON COLUMN "config_info_gray"."gray_rule" IS 'gray_rule';
COMMENT ON COLUMN "config_info_gray"."encrypted_data_key" IS 'encrypted_data_key';
COMMENT ON TABLE "config_info_gray" IS 'config_info_gray';

-- ----------------------------
-- Table structure for config_info_aggr
-- ----------------------------
DROP TABLE IF EXISTS "config_info_aggr";
CREATE TABLE "config_info_aggr" (
  "id" bigserial NOT NULL,
  "data_id" varchar(255) NOT NULL,
  "group_id" varchar(255) NOT NULL,
  "datum_id" varchar(255) NOT NULL,
  "content" text NOT NULL,
  "gmt_modified" timestamp(6) NOT NULL,
  "app_name" varchar(128),
  "tenant_id" varchar(128)
);
COMMENT ON COLUMN "config_info_aggr"."id" IS 'id';
COMMENT ON COLUMN "config_info_aggr"."data_id" IS 'data_id';
COMMENT ON COLUMN "config_info_aggr"."group_id" IS 'group_id';
COMMENT ON COLUMN "config_info_aggr"."datum_id" IS 'datum_id';
COMMENT ON COLUMN "config_info_aggr"."content" IS 'content';
COMMENT ON COLUMN "config_info_aggr"."gmt_modified" IS 'modified time';
COMMENT ON COLUMN "config_info_aggr"."tenant_id" IS 'tenant id';
COMMENT ON TABLE "config_info_aggr" IS 'config_info_aggr';

-- ----------------------------
-- Table structure for config_info_beta
-- ----------------------------
DROP TABLE IF EXISTS "config_info_beta";
CREATE TABLE "config_info_beta" (
  "id" bigserial NOT NULL,
  "data_id" varchar(255) NOT NULL,
  "group_id" varchar(128) NOT NULL,
  "app_name" varchar(128),
  "content" text NOT NULL,
  "beta_ips" varchar(1024),
  "md5" varchar(32),
  "gmt_create" timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "gmt_modified" timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "src_user" text,
  "src_ip" varchar(50),
  "tenant_id" varchar(128),
  "encrypted_data_key" text NOT NULL DEFAULT ''
);
COMMENT ON COLUMN "config_info_beta"."id" IS 'id';
COMMENT ON COLUMN "config_info_beta"."data_id" IS 'data_id';
COMMENT ON COLUMN "config_info_beta"."group_id" IS 'group_id';
COMMENT ON COLUMN "config_info_beta"."app_name" IS 'app_name';
COMMENT ON COLUMN "config_info_beta"."content" IS 'content';
COMMENT ON COLUMN "config_info_beta"."beta_ips" IS 'betaIps';
COMMENT ON COLUMN "config_info_beta"."md5" IS 'md5';
COMMENT ON COLUMN "config_info_beta"."gmt_create" IS 'create time';
COMMENT ON COLUMN "config_info_beta"."gmt_modified" IS 'modified time';
COMMENT ON COLUMN "config_info_beta"."src_user" IS 'source user';
COMMENT ON COLUMN "config_info_beta"."src_ip" IS 'source ip';
COMMENT ON COLUMN "config_info_beta"."tenant_id" IS 'tenant id';
COMMENT ON COLUMN "config_info_beta"."encrypted_data_key" IS 'encrypted data key';
COMMENT ON TABLE "config_info_beta" IS 'config_info_beta';

-- ----------------------------
-- Table structure for config_info_tag
-- ----------------------------
DROP TABLE IF EXISTS "config_info_tag";
CREATE TABLE "config_info_tag" (
  "id" bigserial NOT NULL,
  "data_id" varchar(255) NOT NULL,
  "group_id" varchar(128) NOT NULL,
  "tenant_id" varchar(128),
  "tag_id" varchar(128) NOT NULL,
  "app_name" varchar(128),
  "content" text NOT NULL,
  "md5" varchar(32),
  "gmt_create" timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "gmt_modified" timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "src_user" text,
  "src_ip" varchar(50)
);
COMMENT ON COLUMN "config_info_tag"."id" IS 'id';
COMMENT ON COLUMN "config_info_tag"."data_id" IS 'data_id';
COMMENT ON COLUMN "config_info_tag"."group_id" IS 'group_id';
COMMENT ON COLUMN "config_info_tag"."tenant_id" IS 'tenant_id';
COMMENT ON COLUMN "config_info_tag"."tag_id" IS 'tag_id';
COMMENT ON COLUMN "config_info_tag"."app_name" IS 'app_name';
COMMENT ON COLUMN "config_info_tag"."content" IS 'content';
COMMENT ON COLUMN "config_info_tag"."md5" IS 'md5';
COMMENT ON COLUMN "config_info_tag"."gmt_create" IS 'create time';
COMMENT ON COLUMN "config_info_tag"."gmt_modified" IS 'modified time';
COMMENT ON COLUMN "config_info_tag"."src_user" IS 'source user';
COMMENT ON COLUMN "config_info_tag"."src_ip" IS 'source ip';
COMMENT ON TABLE "config_info_tag" IS 'config_info_tag';

-- ----------------------------
-- Table structure for config_tags_relation
-- ----------------------------
DROP TABLE IF EXISTS "config_tags_relation";
CREATE TABLE "config_tags_relation" (
  "id" bigint NOT NULL,
  "tag_name" varchar(128) NOT NULL,
  "tag_type" varchar(64),
  "data_id" varchar(255) NOT NULL,
  "group_id" varchar(128) NOT NULL,
  "tenant_id" varchar(128),
  "nid" bigserial NOT NULL
);
COMMENT ON COLUMN "config_tags_relation"."id" IS 'id';
COMMENT ON COLUMN "config_tags_relation"."tag_name" IS 'tag_name';
COMMENT ON COLUMN "config_tags_relation"."tag_type" IS 'tag_type';
COMMENT ON COLUMN "config_tags_relation"."data_id" IS 'data_id';
COMMENT ON COLUMN "config_tags_relation"."group_id" IS 'group_id';
COMMENT ON COLUMN "config_tags_relation"."tenant_id" IS 'tenant_id';
COMMENT ON TABLE "config_tags_relation" IS 'config_tag_relation';

-- ----------------------------
-- Table structure for group_capacity
-- ----------------------------
DROP TABLE IF EXISTS "group_capacity";
CREATE TABLE "group_capacity" (
  "id" bigserial NOT NULL,
  "group_id" varchar(128) NOT NULL DEFAULT '',
  "quota" int4 NOT NULL DEFAULT 0,
  "usage" int4 NOT NULL DEFAULT 0,
  "max_size" int4 NOT NULL DEFAULT 0,
  "max_aggr_count" int4 NOT NULL DEFAULT 0,
  "max_aggr_size" int4 NOT NULL DEFAULT 0,
  "max_history_count" int4 NOT NULL DEFAULT 0,
  "gmt_create" timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "gmt_modified" timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON COLUMN "group_capacity"."id" IS 'primary key ID';
COMMENT ON COLUMN "group_capacity"."group_id" IS 'Group ID, empty string means entire cluster';
COMMENT ON COLUMN "group_capacity"."quota" IS 'quota, 0 means use default value';
COMMENT ON COLUMN "group_capacity"."usage" IS 'usage';
COMMENT ON COLUMN "group_capacity"."max_size" IS 'max config size in bytes, 0 means use default value';
COMMENT ON COLUMN "group_capacity"."max_aggr_count" IS 'max aggregation count, 0 means use default value';
COMMENT ON COLUMN "group_capacity"."max_aggr_size" IS 'max aggregation size in bytes, 0 means use default value';
COMMENT ON COLUMN "group_capacity"."max_history_count" IS 'max history count';
COMMENT ON COLUMN "group_capacity"."gmt_create" IS 'create time';
COMMENT ON COLUMN "group_capacity"."gmt_modified" IS 'modified time';
COMMENT ON TABLE "group_capacity" IS 'group_capacity';

-- ----------------------------
-- Table structure for his_config_info
-- ----------------------------
DROP TABLE IF EXISTS "his_config_info";
CREATE TABLE "his_config_info" (
  "id" int8 NOT NULL,
  "nid" bigserial NOT NULL,
  "data_id" varchar(255) NOT NULL,
  "group_id" varchar(128) NOT NULL,
  "app_name" varchar(128),
  "content" text NOT NULL,
  "md5" varchar(32),
  "gmt_create" timestamp(6) NOT NULL DEFAULT '2010-05-05 00:00:00',
  "gmt_modified" timestamp(6) NOT NULL,
  "src_user" text,
  "src_ip" varchar(50),
  "op_type" char(10),
  "tenant_id" varchar(128),
  "encrypted_data_key" text NOT NULL DEFAULT '',
  "publish_type" varchar(50) DEFAULT 'formal',
  "gray_name" varchar(50) DEFAULT NULL,
  "ext_info" text DEFAULT NULL
);
COMMENT ON COLUMN "his_config_info"."app_name" IS 'app_name';
COMMENT ON COLUMN "his_config_info"."tenant_id" IS 'tenant id';
COMMENT ON COLUMN "his_config_info"."encrypted_data_key" IS 'encrypted data key';
COMMENT ON COLUMN "his_config_info"."publish_type" IS 'publish type gray or formal';
COMMENT ON COLUMN "his_config_info"."gray_name" IS 'gray name';
COMMENT ON COLUMN "his_config_info"."ext_info" IS 'ext info';
COMMENT ON TABLE "his_config_info" IS 'his_config_info';

-- ----------------------------
-- Table structure for tenant_capacity
-- ----------------------------
DROP TABLE IF EXISTS "tenant_capacity";
CREATE TABLE "tenant_capacity" (
  "id" bigserial NOT NULL,
  "tenant_id" varchar(128) NOT NULL DEFAULT '',
  "quota" int4 NOT NULL DEFAULT 0,
  "usage" int4 NOT NULL DEFAULT 0,
  "max_size" int4 NOT NULL DEFAULT 0,
  "max_aggr_count" int4 NOT NULL DEFAULT 0,
  "max_aggr_size" int4 NOT NULL DEFAULT 0,
  "max_history_count" int4 NOT NULL DEFAULT 0,
  "gmt_create" timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "gmt_modified" timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON COLUMN "tenant_capacity"."id" IS 'primary key ID';
COMMENT ON COLUMN "tenant_capacity"."tenant_id" IS 'Tenant ID';
COMMENT ON COLUMN "tenant_capacity"."quota" IS 'quota, 0 means use default value';
COMMENT ON COLUMN "tenant_capacity"."usage" IS 'usage';
COMMENT ON COLUMN "tenant_capacity"."max_size" IS 'max config size in bytes, 0 means use default value';
COMMENT ON COLUMN "tenant_capacity"."max_aggr_count" IS 'max aggregation count';
COMMENT ON COLUMN "tenant_capacity"."max_aggr_size" IS 'max aggregation size in bytes, 0 means use default value';
COMMENT ON COLUMN "tenant_capacity"."max_history_count" IS 'max history count';
COMMENT ON COLUMN "tenant_capacity"."gmt_create" IS 'create time';
COMMENT ON COLUMN "tenant_capacity"."gmt_modified" IS 'modified time';
COMMENT ON TABLE "tenant_capacity" IS 'tenant_capacity';

-- ----------------------------
-- Table structure for tenant_info
-- ----------------------------
DROP TABLE IF EXISTS "tenant_info";
CREATE TABLE "tenant_info" (
  "id" bigserial NOT NULL,
  "kp" varchar(128) NOT NULL,
  "tenant_id" varchar(128) DEFAULT '',
  "tenant_name" varchar(128) DEFAULT '',
  "tenant_desc" varchar(256),
  "create_source" varchar(32),
  "gmt_create" int8 NOT NULL,
  "gmt_modified" int8 NOT NULL
);
COMMENT ON COLUMN "tenant_info"."id" IS 'id';
COMMENT ON COLUMN "tenant_info"."kp" IS 'kp';
COMMENT ON COLUMN "tenant_info"."tenant_id" IS 'tenant_id';
COMMENT ON COLUMN "tenant_info"."tenant_name" IS 'tenant_name';
COMMENT ON COLUMN "tenant_info"."tenant_desc" IS 'tenant_desc';
COMMENT ON COLUMN "tenant_info"."create_source" IS 'create_source';
COMMENT ON COLUMN "tenant_info"."gmt_create" IS 'create time';
COMMENT ON COLUMN "tenant_info"."gmt_modified" IS 'modified time';
COMMENT ON TABLE "tenant_info" IS 'tenant_info';

-- ----------------------------
-- Table structure for users
-- ----------------------------
DROP TABLE IF EXISTS "users";
CREATE TABLE "users" (
  "username" varchar(50) NOT NULL,
  "password" varchar(500) NOT NULL,
  "enabled" boolean NOT NULL
);

-- ----------------------------
-- Table structure for roles
-- ----------------------------
DROP TABLE IF EXISTS "roles";
CREATE TABLE "roles" (
  "username" varchar(50) NOT NULL,
  "role" varchar(50) NOT NULL
);

-- ----------------------------
-- Table structure for permissions
-- ----------------------------
DROP TABLE IF EXISTS "permissions";
CREATE TABLE "permissions" (
  "role" varchar(50) NOT NULL,
  "resource" varchar(512) NOT NULL,
  "action" varchar(8) NOT NULL
);

-- ----------------------------
-- Records initialization
-- ----------------------------
INSERT INTO "users" VALUES ('nacos', '$2a$10$EuWPZHzz32dJN7jexM34MOeYirDdFAZm2kuWj7VEOJhhZkDrxfvUu', TRUE);
INSERT INTO "roles" VALUES ('nacos', 'ROLE_ADMIN');

-- ----------------------------
-- Primary Keys
-- ----------------------------
ALTER TABLE "config_info" ADD CONSTRAINT "config_info_pkey" PRIMARY KEY ("id");
ALTER TABLE "config_info_gray" ADD CONSTRAINT "config_info_gray_pkey" PRIMARY KEY ("id");
ALTER TABLE "config_info_aggr" ADD CONSTRAINT "config_info_aggr_pkey" PRIMARY KEY ("id");
ALTER TABLE "config_info_beta" ADD CONSTRAINT "config_info_beta_pkey" PRIMARY KEY ("id");
ALTER TABLE "config_info_tag" ADD CONSTRAINT "config_info_tag_pkey" PRIMARY KEY ("id");
ALTER TABLE "config_tags_relation" ADD CONSTRAINT "config_tags_relation_pkey" PRIMARY KEY ("nid");
ALTER TABLE "group_capacity" ADD CONSTRAINT "group_capacity_pkey" PRIMARY KEY ("id");
ALTER TABLE "his_config_info" ADD CONSTRAINT "his_config_info_pkey" PRIMARY KEY ("nid");
ALTER TABLE "tenant_capacity" ADD CONSTRAINT "tenant_capacity_pkey" PRIMARY KEY ("id");
ALTER TABLE "tenant_info" ADD CONSTRAINT "tenant_info_pkey" PRIMARY KEY ("id");
ALTER TABLE "users" ADD CONSTRAINT "users_pkey" PRIMARY KEY ("username");

-- ----------------------------
-- Indexes
-- ----------------------------
CREATE UNIQUE INDEX "uk_configinfo_datagrouptenant" ON "config_info" ("data_id", "group_id", "tenant_id");

CREATE UNIQUE INDEX "uk_configinfogray_datagrouptenantgray" ON "config_info_gray" ("data_id", "group_id", "tenant_id", "gray_name");
CREATE INDEX "idx_configinfogray_dataid_gmt_modified" ON "config_info_gray" ("data_id", "gmt_modified");
CREATE INDEX "idx_configinfogray_gmt_modified" ON "config_info_gray" ("gmt_modified");

CREATE UNIQUE INDEX "uk_configinfoaggr_datagrouptenantdatum" ON "config_info_aggr" ("data_id", "group_id", "tenant_id", "datum_id");

CREATE UNIQUE INDEX "uk_configinfobeta_datagrouptenant" ON "config_info_beta" ("data_id", "group_id", "tenant_id");

CREATE UNIQUE INDEX "uk_configinfotag_datagrouptenanttag" ON "config_info_tag" ("data_id", "group_id", "tenant_id", "tag_id");

CREATE INDEX "idx_config_tags_tenant_id" ON "config_tags_relation" ("tenant_id");
CREATE UNIQUE INDEX "uk_configtagrelation_configidtag" ON "config_tags_relation" ("id", "tag_name", "tag_type");

CREATE UNIQUE INDEX "uk_group_id" ON "group_capacity" ("group_id");

CREATE INDEX "idx_his_config_info_did" ON "his_config_info" ("data_id");
CREATE INDEX "idx_his_config_info_gmt_create" ON "his_config_info" ("gmt_create");
CREATE INDEX "idx_his_config_info_gmt_modified" ON "his_config_info" ("gmt_modified");

CREATE UNIQUE INDEX "uk_tenant_capacity_tenant_id" ON "tenant_capacity" ("tenant_id");

CREATE UNIQUE INDEX "uk_tenant_info_kptenantid" ON "tenant_info" ("kp", "tenant_id");
CREATE INDEX "idx_tenant_info_tenant_id" ON "tenant_info" ("tenant_id");

CREATE UNIQUE INDEX "uk_username_role" ON "roles" ("username", "role");

CREATE UNIQUE INDEX "uk_role_permission" ON "permissions" ("role", "resource", "action");
