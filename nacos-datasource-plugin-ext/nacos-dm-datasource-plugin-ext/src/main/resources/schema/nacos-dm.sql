CREATE TABLE "NACOS"."USERS"
(
    "USERNAME" VARCHAR(50)  NOT NULL,
    "PASSWORD" VARCHAR(500) NOT NULL,
    "ENABLED"  TINYINT      NOT NULL
);
CREATE TABLE "NACOS"."TENANT_INFO"
(
    "ID"            BIGINT IDENTITY(1,1) NOT NULL,
    "KP"            VARCHAR(128) NOT NULL,
    "TENANT_ID"     VARCHAR(128) DEFAULT ''
        NULL,
    "TENANT_NAME"   VARCHAR(128) DEFAULT ''
        NULL,
    "TENANT_DESC"   VARCHAR(256) NULL,
    "CREATE_SOURCE" VARCHAR(32) NULL,
    "GMT_CREATE"    BIGINT       NOT NULL,
    "GMT_MODIFIED"  BIGINT       NOT NULL
);
CREATE TABLE "NACOS"."TENANT_CAPACITY"
(
    "ID"                BIGINT IDENTITY(1,1) NOT NULL,
    "TENANT_ID"         VARCHAR(128) DEFAULT ''
        NOT NULL,
    "QUOTA"             BIGINT       DEFAULT 0
        NOT NULL,
    "USAGE"             BIGINT       DEFAULT 0
        NOT NULL,
    "MAX_SIZE"          BIGINT       DEFAULT 0
        NOT NULL,
    "MAX_AGGR_COUNT"    BIGINT       DEFAULT 0
        NOT NULL,
    "MAX_AGGR_SIZE"     BIGINT       DEFAULT 0
        NOT NULL,
    "MAX_HISTORY_COUNT" BIGINT       DEFAULT 0
        NOT NULL,
    "GMT_CREATE"        TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP()
        NOT NULL,
    "GMT_MODIFIED"      TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP()
        NOT NULL
);
CREATE TABLE "NACOS"."ROLES"
(
    "USERNAME" VARCHAR(50) NOT NULL,
    "ROLE"     VARCHAR(50) NOT NULL
);
CREATE TABLE "NACOS"."PERMISSIONS"
(
    "ROLE"     VARCHAR(50)  NOT NULL,
    "RESOURCE" VARCHAR(255) NOT NULL,
    "ACTION"   VARCHAR(8)   NOT NULL
);
CREATE TABLE "NACOS"."HIS_CONFIG_INFO"
(
    "ID"                 DECIMAL(20, 0) NOT NULL,
    "NID"                BIGINT IDENTITY(1,1) NOT NULL,
    "DATA_ID"            VARCHAR(255)   NOT NULL,
    "GROUP_ID"           VARCHAR(128)   NOT NULL,
    "APP_NAME"           VARCHAR(128) NULL,
    "CONTENT"            CLOB           NOT NULL,
    "MD5"                VARCHAR(32) NULL,
    "GMT_CREATE"         TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP()
                                        NOT NULL,
    "GMT_MODIFIED"       TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP()
                                        NOT NULL,
    "SRC_USER"           TEXT NULL,
    "SRC_IP"             VARCHAR(50) NULL,
    "OP_TYPE"            CHAR(10) NULL,
    "TENANT_ID"          VARCHAR(128) DEFAULT ''
        NULL,
    "ENCRYPTED_DATA_KEY" TEXT           NOT NULL
);
CREATE TABLE "NACOS"."GROUP_CAPACITY"
(
    "ID"                BIGINT IDENTITY(1,1) NOT NULL,
    "GROUP_ID"          VARCHAR(128) DEFAULT ''
        NOT NULL,
    "QUOTA"             BIGINT       DEFAULT 0
        NOT NULL,
    "USAGE"             BIGINT       DEFAULT 0
        NOT NULL,
    "MAX_SIZE"          BIGINT       DEFAULT 0
        NOT NULL,
    "MAX_AGGR_COUNT"    BIGINT       DEFAULT 0
        NOT NULL,
    "MAX_AGGR_SIZE"     BIGINT       DEFAULT 0
        NOT NULL,
    "MAX_HISTORY_COUNT" BIGINT       DEFAULT 0
        NOT NULL,
    "GMT_CREATE"        TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP()
        NOT NULL,
    "GMT_MODIFIED"      TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP()
        NOT NULL
);
CREATE TABLE "NACOS"."CONFIG_TAGS_RELATION"
(
    "ID"        BIGINT       NOT NULL,
    "TAG_NAME"  VARCHAR(128) NOT NULL,
    "TAG_TYPE"  VARCHAR(64) NULL,
    "DATA_ID"   VARCHAR(255) NOT NULL,
    "GROUP_ID"  VARCHAR(128) NOT NULL,
    "TENANT_ID" VARCHAR(128) DEFAULT ''
        NULL,
    "NID"       BIGINT IDENTITY(1,1) NOT NULL
);
CREATE TABLE "NACOS"."CONFIG_INFO_TAG"
(
    "ID"           BIGINT IDENTITY(1,1) NOT NULL,
    "DATA_ID"      VARCHAR(255) NOT NULL,
    "GROUP_ID"     VARCHAR(128) NOT NULL,
    "TENANT_ID"    VARCHAR(128) DEFAULT ''
        NULL,
    "TAG_ID"       VARCHAR(128) NOT NULL,
    "APP_NAME"     VARCHAR(128) NULL,
    "CONTENT"      CLOB         NOT NULL,
    "MD5"          VARCHAR(32) NULL,
    "GMT_CREATE"   TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP()
                                NOT NULL,
    "GMT_MODIFIED" TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP()
                                NOT NULL,
    "SRC_USER"     TEXT NULL,
    "SRC_IP"       VARCHAR(50) NULL
);
CREATE TABLE "NACOS"."CONFIG_INFO_BETA"
(
    "ID"                 BIGINT IDENTITY(1,1) NOT NULL,
    "DATA_ID"            VARCHAR(255) NOT NULL,
    "GROUP_ID"           VARCHAR(128) NOT NULL,
    "APP_NAME"           VARCHAR(128) NULL,
    "CONTENT"            CLOB         NOT NULL,
    "BETA_IPS"           VARCHAR(1024) NULL,
    "MD5"                VARCHAR(32) NULL,
    "GMT_CREATE"         TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP()
                                      NOT NULL,
    "GMT_MODIFIED"       TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP()
                                      NOT NULL,
    "SRC_USER"           TEXT NULL,
    "SRC_IP"             VARCHAR(50) NULL,
    "TENANT_ID"          VARCHAR(128) DEFAULT ''
        NULL,
    "ENCRYPTED_DATA_KEY" TEXT         NOT NULL
);
CREATE TABLE "NACOS"."CONFIG_INFO_AGGR"
(
    "ID"           BIGINT IDENTITY(1,1) NOT NULL,
    "DATA_ID"      VARCHAR(255) NOT NULL,
    "GROUP_ID"     VARCHAR(128) NOT NULL,
    "DATUM_ID"     VARCHAR(255) NOT NULL,
    "CONTENT"      CLOB         NOT NULL,
    "GMT_MODIFIED" TIMESTAMP(0) NOT NULL,
    "APP_NAME"     VARCHAR(128) NULL,
    "TENANT_ID"    VARCHAR(128) DEFAULT ''
        NULL
);
CREATE TABLE "NACOS"."CONFIG_INFO"
(
    "ID"                 BIGINT IDENTITY(1,1) NOT NULL,
    "DATA_ID"            VARCHAR(255) NOT NULL,
    "GROUP_ID"           VARCHAR(128) NULL,
    "CONTENT"            CLOB         NOT NULL,
    "MD5"                VARCHAR(32) NULL,
    "GMT_CREATE"         TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP()
                                      NOT NULL,
    "GMT_MODIFIED"       TIMESTAMP(0) DEFAULT CURRENT_TIMESTAMP()
                                      NOT NULL,
    "SRC_USER"           TEXT NULL,
    "SRC_IP"             VARCHAR(50) NULL,
    "APP_NAME"           VARCHAR(128) NULL,
    "TENANT_ID"          VARCHAR(128) DEFAULT ''
        NULL,
    "C_DESC"             VARCHAR(256) NULL,
    "C_USE"              VARCHAR(64) NULL,
    "EFFECT"             VARCHAR(64) NULL,
    "TYPE"               VARCHAR(64) NULL,
    "C_SCHEMA"           TEXT NULL,
    "ENCRYPTED_DATA_KEY" TEXT         NOT NULL
);
ALTER TABLE "NACOS"."USERS"
    ADD CONSTRAINT PRIMARY KEY ("USERNAME");

ALTER TABLE "NACOS"."TENANT_INFO"
    ADD CONSTRAINT PRIMARY KEY ("ID");

ALTER TABLE "NACOS"."TENANT_INFO"
    ADD CONSTRAINT "UK_TENANT_INFO_KPTENANTID" UNIQUE ("KP", "TENANT_ID");

ALTER TABLE "NACOS"."TENANT_CAPACITY"
    ADD CONSTRAINT PRIMARY KEY ("ID");

ALTER TABLE "NACOS"."TENANT_CAPACITY"
    ADD CONSTRAINT "UK_TENANT_ID" UNIQUE ("TENANT_ID");

ALTER TABLE "NACOS"."ROLES"
    ADD CONSTRAINT "IDX_USER_ROLE" UNIQUE ("USERNAME", "ROLE");

ALTER TABLE "NACOS"."PERMISSIONS"
    ADD CONSTRAINT "UK_ROLE_PERMISSION" UNIQUE ("ROLE", "RESOURCE", "ACTION");

ALTER TABLE "NACOS"."HIS_CONFIG_INFO"
    ADD CONSTRAINT PRIMARY KEY ("NID");

ALTER TABLE "NACOS"."GROUP_CAPACITY"
    ADD CONSTRAINT PRIMARY KEY ("ID");

ALTER TABLE "NACOS"."GROUP_CAPACITY"
    ADD CONSTRAINT "UK_GROUP_ID" UNIQUE ("GROUP_ID");

ALTER TABLE "NACOS"."CONFIG_TAGS_RELATION"
    ADD CONSTRAINT PRIMARY KEY ("NID");

ALTER TABLE "NACOS"."CONFIG_TAGS_RELATION"
    ADD CONSTRAINT "UK_CONFIGTAGRELATION_CONFIGIDTAG" UNIQUE ("ID", "TAG_NAME", "TAG_TYPE");

ALTER TABLE "NACOS"."CONFIG_INFO_TAG"
    ADD CONSTRAINT PRIMARY KEY ("ID");

ALTER TABLE "NACOS"."CONFIG_INFO_TAG"
    ADD CONSTRAINT "UK_CONFIGINFOTAG_DATAGROUPTENANTTAG" UNIQUE ("DATA_ID", "GROUP_ID", "TENANT_ID", "TAG_ID");

ALTER TABLE "NACOS"."CONFIG_INFO_BETA"
    ADD CONSTRAINT PRIMARY KEY ("ID");

ALTER TABLE "NACOS"."CONFIG_INFO_BETA"
    ADD CONSTRAINT "UK_CONFIGINFOBETA_DATAGROUPTENANT" UNIQUE ("DATA_ID", "GROUP_ID", "TENANT_ID");

ALTER TABLE "NACOS"."CONFIG_INFO_AGGR"
    ADD CONSTRAINT PRIMARY KEY ("ID");

ALTER TABLE "NACOS"."CONFIG_INFO_AGGR"
    ADD CONSTRAINT "UK_CONFIGINFOAGGR_DATAGROUPTENANTDATUM" UNIQUE ("DATA_ID", "GROUP_ID", "TENANT_ID", "DATUM_ID");

ALTER TABLE "NACOS"."CONFIG_INFO"
    ADD CONSTRAINT PRIMARY KEY ("ID");

ALTER TABLE "NACOS"."CONFIG_INFO"
    ADD CONSTRAINT "UK_CONFIGINFO_DATAGROUPTENANT" UNIQUE ("DATA_ID", "GROUP_ID", "TENANT_ID");

CREATE INDEX "IDX_TENANT_ID"
    ON "NACOS"."TENANT_INFO" ("TENANT_ID");

COMMENT
ON TABLE "NACOS"."TENANT_INFO" IS 'tenant_info';

COMMENT
ON COLUMN "NACOS"."TENANT_INFO"."ID" IS 'id';

COMMENT
ON COLUMN "NACOS"."TENANT_INFO"."KP" IS 'kp';

COMMENT
ON COLUMN "NACOS"."TENANT_INFO"."TENANT_ID" IS 'tenant_id';

COMMENT
ON COLUMN "NACOS"."TENANT_INFO"."TENANT_NAME" IS 'tenant_name';

COMMENT
ON COLUMN "NACOS"."TENANT_INFO"."TENANT_DESC" IS 'tenant_desc';

COMMENT
ON COLUMN "NACOS"."TENANT_INFO"."CREATE_SOURCE" IS 'create_source';

COMMENT
ON COLUMN "NACOS"."TENANT_INFO"."GMT_CREATE" IS '创建时间';

COMMENT
ON COLUMN "NACOS"."TENANT_INFO"."GMT_MODIFIED" IS '修改时间';

ALTER TABLE "NACOS"."TENANT_CAPACITY"
    ADD CHECK ("QUOTA" >= 0) ENABLE;

ALTER TABLE "NACOS"."TENANT_CAPACITY"
    ADD CHECK ("MAX_HISTORY_COUNT" >= 0) ENABLE;

ALTER TABLE "NACOS"."TENANT_CAPACITY"
    ADD CHECK ("MAX_AGGR_SIZE" >= 0) ENABLE;

ALTER TABLE "NACOS"."TENANT_CAPACITY"
    ADD CHECK ("MAX_AGGR_COUNT" >= 0) ENABLE;

ALTER TABLE "NACOS"."TENANT_CAPACITY"
    ADD CHECK ("MAX_SIZE" >= 0) ENABLE;

ALTER TABLE "NACOS"."TENANT_CAPACITY"
    ADD CHECK ("USAGE" >= 0) ENABLE;

COMMENT
ON TABLE "NACOS"."TENANT_CAPACITY" IS '租户容量信息表';

COMMENT
ON COLUMN "NACOS"."TENANT_CAPACITY"."ID" IS '主键ID';

COMMENT
ON COLUMN "NACOS"."TENANT_CAPACITY"."TENANT_ID" IS 'Tenant ID';

COMMENT
ON COLUMN "NACOS"."TENANT_CAPACITY"."QUOTA" IS '配额，0表示使用默认值';

COMMENT
ON COLUMN "NACOS"."TENANT_CAPACITY"."USAGE" IS '使用量';

COMMENT
ON COLUMN "NACOS"."TENANT_CAPACITY"."MAX_SIZE" IS '单个配置大小上限，单位为字节，0表示使用默认值';

COMMENT
ON COLUMN "NACOS"."TENANT_CAPACITY"."MAX_AGGR_COUNT" IS '聚合子配置最大个数';

COMMENT
ON COLUMN "NACOS"."TENANT_CAPACITY"."MAX_AGGR_SIZE" IS '单个聚合数据的子配置大小上限，单位为字节，0表示使用默认值';

COMMENT
ON COLUMN "NACOS"."TENANT_CAPACITY"."MAX_HISTORY_COUNT" IS '最大变更历史数量';

COMMENT
ON COLUMN "NACOS"."TENANT_CAPACITY"."GMT_CREATE" IS '创建时间';

COMMENT
ON COLUMN "NACOS"."TENANT_CAPACITY"."GMT_MODIFIED" IS '修改时间';

ALTER TABLE "NACOS"."HIS_CONFIG_INFO"
    ADD CHECK ("ID" >= 0) ENABLE;

CREATE INDEX "IDX_GMT_MODIFIED"
    ON "NACOS"."HIS_CONFIG_INFO" ("GMT_MODIFIED");

CREATE INDEX "IDX_GMT_CREATE"
    ON "NACOS"."HIS_CONFIG_INFO" ("GMT_CREATE");

CREATE INDEX "IDX_DID"
    ON "NACOS"."HIS_CONFIG_INFO" ("DATA_ID");

COMMENT
ON TABLE "NACOS"."HIS_CONFIG_INFO" IS '多租户改造';

COMMENT
ON COLUMN "NACOS"."HIS_CONFIG_INFO"."APP_NAME" IS 'app_name';

COMMENT
ON COLUMN "NACOS"."HIS_CONFIG_INFO"."TENANT_ID" IS '租户字段';

COMMENT
ON COLUMN "NACOS"."HIS_CONFIG_INFO"."ENCRYPTED_DATA_KEY" IS '密钥';

ALTER TABLE "NACOS"."GROUP_CAPACITY"
    ADD CHECK ("QUOTA" >= 0) ENABLE;

ALTER TABLE "NACOS"."GROUP_CAPACITY"
    ADD CHECK ("MAX_HISTORY_COUNT" >= 0) ENABLE;

ALTER TABLE "NACOS"."GROUP_CAPACITY"
    ADD CHECK ("MAX_AGGR_SIZE" >= 0) ENABLE;

ALTER TABLE "NACOS"."GROUP_CAPACITY"
    ADD CHECK ("MAX_AGGR_COUNT" >= 0) ENABLE;

ALTER TABLE "NACOS"."GROUP_CAPACITY"
    ADD CHECK ("MAX_SIZE" >= 0) ENABLE;

ALTER TABLE "NACOS"."GROUP_CAPACITY"
    ADD CHECK ("USAGE" >= 0) ENABLE;

COMMENT
ON TABLE "NACOS"."GROUP_CAPACITY" IS '集群、各Group容量信息表';

COMMENT
ON COLUMN "NACOS"."GROUP_CAPACITY"."ID" IS '主键ID';

COMMENT
ON COLUMN "NACOS"."GROUP_CAPACITY"."GROUP_ID" IS 'Group ID，空字符表示整个集群';

COMMENT
ON COLUMN "NACOS"."GROUP_CAPACITY"."QUOTA" IS '配额，0表示使用默认值';

COMMENT
ON COLUMN "NACOS"."GROUP_CAPACITY"."USAGE" IS '使用量';

COMMENT
ON COLUMN "NACOS"."GROUP_CAPACITY"."MAX_SIZE" IS '单个配置大小上限，单位为字节，0表示使用默认值';

COMMENT
ON COLUMN "NACOS"."GROUP_CAPACITY"."MAX_AGGR_COUNT" IS '聚合子配置最大个数，，0表示使用默认值';

COMMENT
ON COLUMN "NACOS"."GROUP_CAPACITY"."MAX_AGGR_SIZE" IS '单个聚合数据的子配置大小上限，单位为字节，0表示使用默认值';

COMMENT
ON COLUMN "NACOS"."GROUP_CAPACITY"."MAX_HISTORY_COUNT" IS '最大变更历史数量';

COMMENT
ON COLUMN "NACOS"."GROUP_CAPACITY"."GMT_CREATE" IS '创建时间';

COMMENT
ON COLUMN "NACOS"."GROUP_CAPACITY"."GMT_MODIFIED" IS '修改时间';

COMMENT
ON TABLE "NACOS"."CONFIG_TAGS_RELATION" IS 'config_tag_relation';

COMMENT
ON COLUMN "NACOS"."CONFIG_TAGS_RELATION"."ID" IS 'id';

COMMENT
ON COLUMN "NACOS"."CONFIG_TAGS_RELATION"."TAG_NAME" IS 'tag_name';

COMMENT
ON COLUMN "NACOS"."CONFIG_TAGS_RELATION"."TAG_TYPE" IS 'tag_type';

COMMENT
ON COLUMN "NACOS"."CONFIG_TAGS_RELATION"."DATA_ID" IS 'data_id';

COMMENT
ON COLUMN "NACOS"."CONFIG_TAGS_RELATION"."GROUP_ID" IS 'group_id';

COMMENT
ON COLUMN "NACOS"."CONFIG_TAGS_RELATION"."TENANT_ID" IS 'tenant_id';

COMMENT
ON TABLE "NACOS"."CONFIG_INFO_TAG" IS 'config_info_tag';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO_TAG"."ID" IS 'id';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO_TAG"."DATA_ID" IS 'data_id';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO_TAG"."GROUP_ID" IS 'group_id';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO_TAG"."TENANT_ID" IS 'tenant_id';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO_TAG"."TAG_ID" IS 'tag_id';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO_TAG"."APP_NAME" IS 'app_name';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO_TAG"."CONTENT" IS 'content';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO_TAG"."MD5" IS 'md5';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO_TAG"."GMT_CREATE" IS '创建时间';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO_TAG"."GMT_MODIFIED" IS '修改时间';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO_TAG"."SRC_USER" IS 'source user';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO_TAG"."SRC_IP" IS 'source ip';

COMMENT
ON TABLE "NACOS"."CONFIG_INFO_BETA" IS 'config_info_beta';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO_BETA"."ID" IS 'id';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO_BETA"."DATA_ID" IS 'data_id';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO_BETA"."GROUP_ID" IS 'group_id';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO_BETA"."APP_NAME" IS 'app_name';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO_BETA"."CONTENT" IS 'content';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO_BETA"."BETA_IPS" IS 'betaIps';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO_BETA"."MD5" IS 'md5';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO_BETA"."GMT_CREATE" IS '创建时间';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO_BETA"."GMT_MODIFIED" IS '修改时间';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO_BETA"."SRC_USER" IS 'source user';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO_BETA"."SRC_IP" IS 'source ip';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO_BETA"."TENANT_ID" IS '租户字段';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO_BETA"."ENCRYPTED_DATA_KEY" IS '密钥';

COMMENT
ON TABLE "NACOS"."CONFIG_INFO_AGGR" IS '增加租户字段';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO_AGGR"."ID" IS 'id';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO_AGGR"."DATA_ID" IS 'data_id';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO_AGGR"."GROUP_ID" IS 'group_id';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO_AGGR"."DATUM_ID" IS 'datum_id';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO_AGGR"."CONTENT" IS '内容';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO_AGGR"."GMT_MODIFIED" IS '修改时间';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO_AGGR"."TENANT_ID" IS '租户字段';

COMMENT
ON TABLE "NACOS"."CONFIG_INFO" IS 'config_info';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO"."ID" IS 'id';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO"."DATA_ID" IS 'data_id';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO"."CONTENT" IS 'content';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO"."MD5" IS 'md5';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO"."GMT_CREATE" IS '创建时间';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO"."GMT_MODIFIED" IS '修改时间';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO"."SRC_USER" IS 'source user';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO"."SRC_IP" IS 'source ip';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO"."TENANT_ID" IS '租户字段';

COMMENT
ON COLUMN "NACOS"."CONFIG_INFO"."ENCRYPTED_DATA_KEY" IS '密钥';



INSERT INTO "NACOS"."USERS"("USERNAME", "PASSWORD", "ENABLED")
VALUES ('nacos', '$2a$10$EuWPZHzz32dJN7jexM34MOeYirDdFAZm2kuWj7VEOJhhZkDrxfvUu', 1);

INSERT INTO "NACOS"."ROLES"("USERNAME", "ROLE")
VALUES ('nacos', 'ROLE_ADMIN');

