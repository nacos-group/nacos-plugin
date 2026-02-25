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

package com.alibaba.nacos.plugin.datasource.impl.postgresql;

import com.alibaba.nacos.common.utils.CollectionUtils;
import com.alibaba.nacos.common.utils.StringUtils;
import com.alibaba.nacos.plugin.datasource.constants.FieldConstant;
import com.alibaba.nacos.plugin.datasource.mapper.ConfigInfoMapper;
import com.alibaba.nacos.plugin.datasource.model.MapperContext;
import com.alibaba.nacos.plugin.datasource.model.MapperResult;

import java.sql.Timestamp;
import java.util.ArrayList;
import java.util.List;

import static com.alibaba.nacos.api.common.Constants.DEFAULT_NAMESPACE_ID;

/**
 * The postgresql implementation of ConfigInfoMapper.
 *
 * @author Long Yu
 * @author Ken
 **/
public class ConfigInfoMapperByPostgresql extends AbstractMapperByPostgresql implements ConfigInfoMapper {
    
    private String getLimitPageSqlWithMark(String sql) {
        return getDatabaseDialect().getLimitPageSqlWithMark(sql);
    }
    
    @Override
    public MapperResult findConfigInfoByAppFetchRows(MapperContext context) {
        final String appName = (String) context.getWhereParameter(FieldConstant.APP_NAME);
        final String tenantId = (String) context.getWhereParameter(FieldConstant.TENANT_ID);
        
        List<Object> sqlArgs = new ArrayList<>();
        String sql = "SELECT id,data_id,group_id,tenant_id,app_name,content FROM config_info";
        if (StringUtils.isBlank(tenantId)) {
            sql += " tenant_id='" + DEFAULT_NAMESPACE_ID + "' ";
        } else {
            sql += " tenant_id LIKE ? ";
            sqlArgs.add(tenantId);
        }
        sql += " AND app_name= ?";
        sqlArgs.add(appName);
        
        sql = getLimitPageSqlWithMark(sql);
        
        sqlArgs.add(context.getStartRow());
        sqlArgs.add(context.getPageSize());
        return new MapperResult(sql, sqlArgs);
    }
    
    @Override
    public MapperResult getTenantIdList(MapperContext context) {
        String sql = getLimitPageSqlWithMark(
                "SELECT tenant_id FROM config_info WHERE tenant_id != '" + DEFAULT_NAMESPACE_ID
                        + "' GROUP BY tenant_id ");
        return new MapperResult(sql, CollectionUtils.list(context.getStartRow(), context.getPageSize()));
    }
    
    @Override
    public MapperResult getGroupIdList(MapperContext context) {
        String sql = getLimitPageSqlWithMark(
                "SELECT group_id FROM config_info WHERE tenant_id != '" + DEFAULT_NAMESPACE_ID
                        + "' GROUP BY group_id ");
        return new MapperResult(sql, CollectionUtils.list(context.getStartRow(), context.getPageSize()));
    }
    
    @Override
    public MapperResult findAllConfigKey(MapperContext context) {
        int startRow = context.getStartRow();
        int pageSize = context.getPageSize();
        
        String tenantId = (String) context.getWhereParameter(FieldConstant.TENANT_ID);
        
        List<Object> sqlArgs = new ArrayList<>();
        StringBuilder innerSqlBuilder = new StringBuilder(" SELECT id FROM config_info WHERE ");
        if (StringUtils.isBlank(tenantId)) {
            innerSqlBuilder.append(" tenant_id='").append(DEFAULT_NAMESPACE_ID).append("' ");
        } else {
            innerSqlBuilder.append(" tenant_id LIKE ? ");
            sqlArgs.add(tenantId);
        }
        innerSqlBuilder.append(" ORDER BY id ");
        
        String subQuery = getLimitPageSqlWithMark(innerSqlBuilder.toString());
        
        sqlArgs.add(startRow);
        sqlArgs.add(pageSize);
        
        String sql = " SELECT data_id,group_id,app_name  FROM ( " + subQuery + " )"
                + " g, config_info t WHERE g.id = t.id  ";
        return new MapperResult(sql, sqlArgs);
    }
    
    @Override
    public MapperResult findAllConfigInfoBaseFetchRows(MapperContext context) {
        int startRow = context.getStartRow();
        int pageSize = context.getPageSize();
        String innerSql = getLimitPageSqlWithMark(" SELECT id FROM config_info ORDER BY id ");
        String sql = " SELECT t.id,data_id,group_id,content,md5 " + " FROM ( " + innerSql + "  ) "
                + " g, config_info t  WHERE g.id = t.id ";
        return new MapperResult(sql, CollectionUtils.list(startRow, pageSize));
    }
    
    @Override
    public MapperResult findAllConfigInfoFragment(MapperContext context) {
        int startRow = context.getStartRow();
        int pageSize = context.getPageSize();
        String sql = getLimitPageSqlWithMark(
                "SELECT id,data_id,group_id,tenant_id,app_name,content,md5,gmt_modified,type,encrypted_data_key "
                        + "FROM config_info WHERE id > ? ORDER BY id ASC ");
        return new MapperResult(sql,
                CollectionUtils.list(context.getWhereParameter(FieldConstant.ID), startRow, pageSize));
    }
    
    @Override
    public MapperResult findChangeConfigFetchRows(MapperContext context) {
        final String tenant = (String) context.getWhereParameter(FieldConstant.TENANT_ID);
        final String dataId = (String) context.getWhereParameter(FieldConstant.DATA_ID);
        final String group = (String) context.getWhereParameter(FieldConstant.GROUP_ID);
        final String appName = (String) context.getWhereParameter(FieldConstant.APP_NAME);
        final String tenantTmp = StringUtils.isBlank(tenant) ? StringUtils.EMPTY : tenant;
        final Timestamp startTime = (Timestamp) context.getWhereParameter(FieldConstant.START_TIME);
        final Timestamp endTime = (Timestamp) context.getWhereParameter(FieldConstant.END_TIME);
        final long lastMaxId = (long) context.getWhereParameter(FieldConstant.LAST_MAX_ID);
        List<Object> paramList = new ArrayList<>();
        
        final String sqlFetchRows = "SELECT id,data_id,group_id,tenant_id,app_name,content,type,md5,gmt_modified FROM config_info WHERE ";
        String where = " 1=1 ";
        if (!StringUtils.isBlank(dataId)) {
            where += " AND data_id LIKE ? ";
            paramList.add(dataId);
        }
        if (!StringUtils.isBlank(group)) {
            where += " AND group_id LIKE ? ";
            paramList.add(group);
        }
        if (!StringUtils.isBlank(tenantTmp)) {
            where += " AND tenant_id = ? ";
            paramList.add(tenantTmp);
        }
        if (!StringUtils.isBlank(appName)) {
            where += " AND app_name = ? ";
            paramList.add(appName);
        }
        if (startTime != null) {
            where += " AND gmt_modified >=? ";
            paramList.add(startTime);
        }
        if (endTime != null) {
            where += " AND gmt_modified <=? ";
            paramList.add(endTime);
        }
        String originSql = sqlFetchRows + where + " AND id > " + lastMaxId + " ORDER BY id ASC";
        String sql = getLimitPageSqlWithMark(originSql);
        paramList.add(context.getStartRow());
        paramList.add(context.getPageSize());
        return new MapperResult(sql, paramList);
    }
    
    @Override
    public MapperResult listGroupKeyMd5ByPageFetchRows(MapperContext context) {
        int startRow = context.getStartRow();
        int pageSize = context.getPageSize();
        String innerSql = getLimitPageSqlWithMark(" SELECT id FROM config_info ORDER BY id ");
        String sql =
                " SELECT t.id,data_id,group_id,tenant_id,app_name,md5,type,gmt_modified,encrypted_data_key FROM " + "( "
                        + innerSql + " ) g, config_info t WHERE g.id = t.id";
        return new MapperResult(sql, CollectionUtils.list(startRow, pageSize));
    }
    
    @Override
    public MapperResult findConfigInfoBaseLikeFetchRows(MapperContext context) {
        final String dataId = (String) context.getWhereParameter(FieldConstant.DATA_ID);
        final String group = (String) context.getWhereParameter(FieldConstant.GROUP_ID);
        final String content = (String) context.getWhereParameter(FieldConstant.CONTENT);
        final String sqlFetchRows = "SELECT id,data_id,group_id,tenant_id,content FROM config_info WHERE ";
        String where = " tenant_id='" + DEFAULT_NAMESPACE_ID + "' ";
        List<Object> paramList = new ArrayList<>();
        if (!StringUtils.isBlank(dataId)) {
            where += " AND data_id LIKE ? ";
            paramList.add(dataId);
        }
        if (!StringUtils.isBlank(group)) {
            where += " AND group_id LIKE ? ";
            paramList.add(group);
        }
        if (!StringUtils.isBlank(content)) {
            where += " AND content LIKE ? ";
            paramList.add(content);
        }
        
        paramList.add(context.getStartRow());
        paramList.add(context.getPageSize());
        
        String sql = getLimitPageSqlWithMark(sqlFetchRows + where);
        return new MapperResult(sql, paramList);
    }
    
    /**
     * {@inheritDoc}
     */
    @Override
    public MapperResult findConfigInfo4PageFetchRows(MapperContext context) {
        final String tenant = (String) context.getWhereParameter(FieldConstant.TENANT_ID);
        final String dataId = (String) context.getWhereParameter(FieldConstant.DATA_ID);
        final String group = (String) context.getWhereParameter(FieldConstant.GROUP_ID);
        final String appName = (String) context.getWhereParameter(FieldConstant.APP_NAME);
        final String content = (String) context.getWhereParameter(FieldConstant.CONTENT);
        List<Object> paramList = new ArrayList<>();
        final String sql = "SELECT id,data_id,group_id,tenant_id,app_name,content,type,encrypted_data_key FROM config_info";
        StringBuilder where = new StringBuilder(" WHERE ");
        
        where.append(" tenant_id=COALESCE(?, '").append(DEFAULT_NAMESPACE_ID).append("') ");
        paramList.add(tenant);
        
        if (StringUtils.isNotBlank(dataId)) {
            where.append(" AND data_id=? ");
            paramList.add(dataId);
        }
        if (StringUtils.isNotBlank(group)) {
            where.append(" AND group_id=? ");
            paramList.add(group);
        }
        if (StringUtils.isNotBlank(appName)) {
            where.append(" AND app_name=? ");
            paramList.add(appName);
        }
        if (!StringUtils.isBlank(content)) {
            where.append(" AND content LIKE ? ");
            paramList.add(content);
        }
        
        paramList.add(context.getStartRow());
        paramList.add(context.getPageSize());
        
        String resultSql = getLimitPageSqlWithMark(sql + where);
        return new MapperResult(resultSql, paramList);
    }
    
    @Override
    public MapperResult findConfigInfoBaseByGroupFetchRows(MapperContext context) {
        int startRow = context.getStartRow();
        int pageSize = context.getPageSize();
        
        String groupId = (String) context.getWhereParameter(FieldConstant.GROUP_ID);
        String tenantId = (String) context.getWhereParameter(FieldConstant.TENANT_ID);
        
        List<Object> sqlArgs = new ArrayList<>();
        sqlArgs.add(groupId);
        sqlArgs.add(tenantId);
        sqlArgs.add(startRow);
        sqlArgs.add(pageSize);
        String sql =
                "SELECT id,data_id,group_id,content FROM config_info WHERE group_id=? and " + " tenant_id=COALESCE(?, '"
                        + DEFAULT_NAMESPACE_ID + "') ";
        String resultSql = getLimitPageSqlWithMark(sql);
        
        return new MapperResult(resultSql, sqlArgs);
    }
    
    /**
     * {@inheritDoc}
     */
    @Override
    public MapperResult findConfigInfoLike4PageFetchRows(MapperContext context) {
        final String tenant = (String) context.getWhereParameter(FieldConstant.TENANT_ID);
        final String dataId = (String) context.getWhereParameter(FieldConstant.DATA_ID);
        final String group = (String) context.getWhereParameter(FieldConstant.GROUP_ID);
        final String appName = (String) context.getWhereParameter(FieldConstant.APP_NAME);
        final String content = (String) context.getWhereParameter(FieldConstant.CONTENT);
        final String sqlFetchRows =
                "SELECT " + " id,data_id,group_id,tenant_id,app_name,content,encrypted_data_key,md5,type "
                        + "FROM config_info";
        StringBuilder where = new StringBuilder(" WHERE ");
        List<Object> paramList = new ArrayList<>();
        
        if (StringUtils.isBlank(tenant)) {
            where.append(" tenant_id='").append(DEFAULT_NAMESPACE_ID).append("' ");
        } else {
            where.append(" tenant_id LIKE ? ");
            paramList.add(tenant);
        }
        
        if (!StringUtils.isBlank(dataId)) {
            where.append(" AND data_id LIKE ? ");
            paramList.add(dataId);
        }
        if (!StringUtils.isBlank(group)) {
            where.append(" AND group_id LIKE ? ");
            paramList.add(group);
        }
        if (!StringUtils.isBlank(appName)) {
            where.append(" AND app_name = ? ");
            paramList.add(appName);
        }
        if (!StringUtils.isBlank(content)) {
            where.append(" AND content LIKE ? ");
            paramList.add(content);
        }
        paramList.add(context.getStartRow());
        paramList.add(context.getPageSize());
        
        String sql = getLimitPageSqlWithMark(sqlFetchRows + where);
        return new MapperResult(sql, paramList);
    }
    
    @Override
    public MapperResult findAllConfigInfoFetchRows(MapperContext context) {
        String tenantId = (String) context.getWhereParameter(FieldConstant.TENANT_ID);
        
        List<Object> sqlArgs = new ArrayList<>();
        StringBuilder sqlBuilder = new StringBuilder("SELECT id FROM config_info WHERE ");
        if (StringUtils.isBlank(tenantId)) {
            sqlBuilder.append(" tenant_id='").append(DEFAULT_NAMESPACE_ID).append("' ");
        } else {
            sqlBuilder.append(" tenant_id LIKE ? ");
            sqlArgs.add(tenantId);
        }
        
        sqlBuilder.append(" ORDER BY id ");
        
        sqlArgs.add(context.getStartRow());
        sqlArgs.add(context.getPageSize());
        
        String innerSql = getLimitPageSqlWithMark(sqlBuilder.toString());
        String sql = " SELECT t.id,data_id,group_id,tenant_id,app_name,content,md5 " + " FROM ( " + innerSql + " )"
                + " g, config_info t  WHERE g.id = t.id ";
        return new MapperResult(sql, sqlArgs);
    }
}
