/*
 * Copyright 1999-2022 Alibaba Group Holding Ltd.
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

package com.alibaba.nacos.plugin.datasource.impl.base;

import com.alibaba.nacos.common.utils.StringUtils;
import com.alibaba.nacos.plugin.datasource.constants.TableConstant;
import com.alibaba.nacos.plugin.datasource.dialect.DatabaseDialect;
import com.alibaba.nacos.plugin.datasource.impl.mysql.ConfigInfoMapperByMySql;
import com.alibaba.nacos.plugin.datasource.manager.DatabaseDialectManager;

import java.sql.Timestamp;
import java.util.Map;

/**
 * The base implementation of ConfigInfoMapper.
 *
 * @author Long Yu
 **/
public class BaseConfigInfoMapper extends ConfigInfoMapperByMySql {
    
    private static final String DATA_ID = "dataId";
    
    private static final String GROUP = "group";
    
    private static final String APP_NAME = "appName";
    
    private static final String CONTENT = "content";
    
    private static final String TENANT = "tenant";
    
    private DatabaseDialect databaseDialect;
    
    public BaseConfigInfoMapper() {
        databaseDialect = DatabaseDialectManager.getInstance().getDialect(getDataSource());
    }
    
    public String getLimitPageSqlWithOffset(String sql, int startOffset, int pageSize) {
        return databaseDialect.getLimitPageSqlWithOffset(sql, startOffset, pageSize);
    }
    
    public String getLimitPageSqlWithMark(String sql) {
        return databaseDialect.getLimitPageSqlWithMark(sql);
    }
    
    @Override
    public String findConfigInfoByAppFetchRows(int startRow, int pageSize) {
        return getLimitPageSqlWithOffset("SELECT id,data_id,group_id,tenant_id,app_name,content FROM config_info"
                + " WHERE tenant_id LIKE ? AND app_name= ?",startRow, pageSize);
    }
    
    @Override
    public String getTenantIdList(int startRow, int pageSize) {
        return getLimitPageSqlWithOffset("SELECT tenant_id FROM config_info WHERE tenant_id != '' GROUP BY tenant_id ", startRow, pageSize);
    }
    
    @Override
    public String getGroupIdList(int startRow, int pageSize) {
        return getLimitPageSqlWithOffset("SELECT group_id FROM config_info WHERE tenant_id ='' GROUP BY group_id ", + startRow, pageSize);
    }
    
    @Override
    public String findAllConfigKey(int startRow, int pageSize) {
        String innerSql = getLimitPageSqlWithOffset(" SELECT id FROM config_info WHERE tenant_id LIKE ? ORDER BY id ", startRow, pageSize);
        return " SELECT data_id,group_id,app_name  FROM ( "
                + innerSql
                + " g, config_info t WHERE g.id = t.id  ";
    }
    
    @Override
    public String findAllConfigInfoBaseFetchRows(int startRow, int pageSize) {
        String innerSql = getLimitPageSqlWithMark(" SELECT id FROM config_info ORDER BY id ");
        return " SELECT t.id,data_id,group_id,content,md5"
                + " FROM ( " + innerSql + "  ) "
                + " g, config_info t  WHERE g.id = t.id ";
    }
    
    @Override
    public String findAllConfigInfoFragment(int startRow, int pageSize) {
        return getLimitPageSqlWithOffset("SELECT id,data_id,group_id,tenant_id,app_name,content,md5,gmt_modified,type,encrypted_data_key "
                + "FROM config_info WHERE id > ? ORDER BY id ASC ", startRow, pageSize);
    }
    
    @Override
    public String findChangeConfigFetchRows(Map<String, String> params, final Timestamp startTime,
            final Timestamp endTime, int startRow, int pageSize, long lastMaxId) {
        final String tenant = params.get(TENANT);
        final String dataId = params.get(DATA_ID);
        final String group = params.get(GROUP);
        final String appName = params.get(APP_NAME);
        final String tenantTmp = StringUtils.isBlank(tenant) ? StringUtils.EMPTY : tenant;
        final String sqlFetchRows = "SELECT id,data_id,group_id,tenant_id,app_name,content,type,md5,gmt_modified FROM config_info WHERE ";
        String where = " 1=1 ";
        if (!StringUtils.isBlank(dataId)) {
            where += " AND data_id LIKE ? ";
        }
        if (!StringUtils.isBlank(group)) {
            where += " AND group_id LIKE ? ";
        }
        
        if (!StringUtils.isBlank(tenantTmp)) {
            where += " AND tenant_id = ? ";
        }
        
        if (!StringUtils.isBlank(appName)) {
            where += " AND app_name = ? ";
        }
        if (startTime != null) {
            where += " AND gmt_modified >=? ";
        }
        if (endTime != null) {
            where += " AND gmt_modified <=? ";
        }
        String orignSql = sqlFetchRows + where + " AND id > " + lastMaxId + " ORDER BY id ASC";
        return getLimitPageSqlWithOffset(orignSql,0, pageSize);
    }
    
    @Override
    public String listGroupKeyMd5ByPageFetchRows(int startRow, int pageSize) {
        String innerSql = getLimitPageSqlWithOffset(" SELECT id FROM config_info ORDER BY id ", startRow, pageSize);
        return " SELECT t.id,data_id,group_id,tenant_id,app_name,md5,type,gmt_modified,encrypted_data_key FROM "
                + "( " + innerSql + " ) g, config_info t WHERE g.id = t.id";
    }
    
    @Override
    public String findConfigInfoBaseLikeFetchRows(Map<String, String> params, int startRow, int pageSize) {
        final String sqlFetchRows = "SELECT id,data_id,group_id,tenant_id,content FROM config_info WHERE ";
        String where = " 1=1 AND tenant_id='' ";
        if (!StringUtils.isBlank(params.get(DATA_ID))) {
            where += " AND data_id LIKE ? ";
        }
        if (!StringUtils.isBlank(params.get(GROUP))) {
            where += " AND group_id LIKE ";
        }
        if (!StringUtils.isBlank(params.get(CONTENT))) {
            where += " AND content LIKE ? ";
        }
        return getLimitPageSqlWithOffset(sqlFetchRows + where, startRow, pageSize);
    }
    
    @Override
    public String findConfigInfo4PageFetchRows(Map<String, String> params, int startRow, int pageSize) {
        final String appName = params.get(APP_NAME);
        final String dataId = params.get(DATA_ID);
        final String group = params.get(GROUP);
        final String sql = "SELECT id,data_id,group_id,tenant_id,app_name,content,type,encrypted_data_key FROM config_info";
        StringBuilder where = new StringBuilder(" WHERE ");
        where.append(" tenant_id=? ");
        if (StringUtils.isNotBlank(dataId)) {
            where.append(" AND data_id=? ");
        }
        if (StringUtils.isNotBlank(group)) {
            where.append(" AND group_id=? ");
        }
        if (StringUtils.isNotBlank(appName)) {
            where.append(" AND app_name=? ");
        }
        return getLimitPageSqlWithOffset(sql + where, startRow, pageSize);
    }
    
    @Override
    public String findConfigInfoBaseByGroupFetchRows(int startRow, int pageSize) {
        String sql = "SELECT id,data_id,group_id,content FROM config_info WHERE group_id=? AND tenant_id=? ";
        return getLimitPageSqlWithOffset(sql,startRow, pageSize);
    }
    
    @Override
    public String findConfigInfoLike4PageFetchRows(Map<String, String> params, int startRow, int pageSize) {
        String dataId = params.get(DATA_ID);
        String group = params.get(GROUP);
        final String appName = params.get(APP_NAME);
        final String content = params.get(CONTENT);
        final String sqlFetchRows = "SELECT id,data_id,group_id,tenant_id,app_name,content,encrypted_data_key FROM config_info";
        StringBuilder where = new StringBuilder(" WHERE ");
        where.append(" tenant_id LIKE ? ");
        if (!StringUtils.isBlank(dataId)) {
            where.append(" AND data_id LIKE ? ");
        }
        if (!StringUtils.isBlank(group)) {
            where.append(" AND group_id LIKE ? ");
        }
        if (!StringUtils.isBlank(appName)) {
            where.append(" AND app_name = ? ");
        }
        if (!StringUtils.isBlank(content)) {
            where.append(" AND content LIKE ? ");
        }
        return getLimitPageSqlWithOffset(sqlFetchRows + where, startRow, pageSize);
    }
    
    @Override
    public String findAllConfigInfoFetchRows(int startRow, int pageSize) {
        String innerSql = getLimitPageSqlWithMark("SELECT id FROM config_info WHERE tenant_id LIKE ? ORDER BY id ");
        return " SELECT t.id,data_id,group_id,tenant_id,app_name,content,md5 "
                + " FROM ( " + innerSql + " )"
                + " g, config_info t  WHERE g.id = t.id ";
    }
    
    @Override
    public String getTableName() {
        return TableConstant.CONFIG_INFO;
    }
    
}
