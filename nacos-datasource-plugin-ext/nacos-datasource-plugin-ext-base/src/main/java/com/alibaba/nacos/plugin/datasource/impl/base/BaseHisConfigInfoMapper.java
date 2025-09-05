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

import com.alibaba.nacos.common.utils.CollectionUtils;
import com.alibaba.nacos.common.utils.StringUtils;
import com.alibaba.nacos.plugin.datasource.constants.FieldConstant;
import com.alibaba.nacos.plugin.datasource.dialect.DatabaseDialect;
import com.alibaba.nacos.plugin.datasource.manager.DatabaseDialectManager;
import com.alibaba.nacos.plugin.datasource.mapper.AbstractMapper;
import com.alibaba.nacos.plugin.datasource.mapper.HistoryConfigInfoMapper;
import com.alibaba.nacos.plugin.datasource.mapper.TenantCapacityMapper;
import com.alibaba.nacos.plugin.datasource.model.MapperContext;
import com.alibaba.nacos.plugin.datasource.model.MapperResult;

import java.util.List;

/**
 * The base implementation of TenantCapacityMapper.
 *
 * @author Long Yu
 **/
public abstract class BaseHisConfigInfoMapper extends AbstractMapper implements HistoryConfigInfoMapper {

    private DatabaseDialect databaseDialect;

    public BaseHisConfigInfoMapper() {
        databaseDialect = DatabaseDialectManager.getInstance().getDialect(getDataSource());
    }



    @Override
    public String getFunction(String functionName) {
        return databaseDialect.getFunction(functionName);
    }
    @Override
    public MapperResult removeConfigHistory(MapperContext context) {
        String sql = "DELETE FROM his_config_info WHERE gmt_modified < ? LIMIT ?";
        return new MapperResult(sql, CollectionUtils.list(context.getWhereParameter(FieldConstant.START_TIME),
                context.getWhereParameter(FieldConstant.LIMIT_SIZE)));
    }

    @Override
    public MapperResult pageFindConfigHistoryFetchRows(MapperContext context) {
        String sql = databaseDialect.getLimitPageSqlWithOffset("SELECT nid,data_id,group_id,tenant_id,app_name,src_ip,src_user,op_type,ext_info,publish_type,gray_name,gmt_create,gmt_modified "
                + "FROM " + getTableName()  + " WHERE data_id = ? AND group_id = ? AND tenant_id = ? ORDER BY nid DESC", context.getStartRow(), context.getPageSize());
        return new MapperResult(sql, CollectionUtils.list(context.getWhereParameter(FieldConstant.DATA_ID),
                context.getWhereParameter(FieldConstant.GROUP_ID), context.getWhereParameter(FieldConstant.TENANT_ID)));
    }

    @Override
    public MapperResult findConfigHistoryCountByTime(MapperContext context) {
        return HistoryConfigInfoMapper.super.findConfigHistoryCountByTime(context);
    }

    @Override
    public MapperResult findDeletedConfig(MapperContext context) {
        String sql = databaseDialect.getLimitTopSqlWithMark("SELECT id, nid, data_id, group_id, app_name, content, md5, gmt_create, gmt_modified, src_user, src_ip, op_type, tenant_id, "
                + "publish_type, gray_name, ext_info, encrypted_data_key FROM " + getTableName() + " WHERE op_type = 'D' AND "
                + "publish_type = ? and gmt_modified >= ? and nid > ? order by nid ");
        return new MapperResult(sql,
                CollectionUtils.list(context.getWhereParameter(FieldConstant.PUBLISH_TYPE),
                        context.getWhereParameter(FieldConstant.START_TIME),
                        context.getWhereParameter(FieldConstant.LAST_MAX_ID),
                        context.getWhereParameter(FieldConstant.PAGE_SIZE)));
    }

    @Override
    public MapperResult findConfigHistoryFetchRows(MapperContext context) {
        return HistoryConfigInfoMapper.super.findConfigHistoryFetchRows(context);
    }

    @Override
    public MapperResult detailPreviousConfigHistory(MapperContext context) {
        return HistoryConfigInfoMapper.super.detailPreviousConfigHistory(context);
    }

    @Override
    public MapperResult getNextHistoryInfo(MapperContext context) {
        String sql = databaseDialect.getLimitPageSql("SELECT nid,data_id,group_id,tenant_id,app_name,content,md5,src_user,src_ip,op_type,publish_type,"
                + "gray_name,ext_info,gmt_create,gmt_modified,encrypted_data_key FROM " + getTableName()
                + " WHERE data_id = ? AND group_id = ? AND tenant_id = ? AND publish_type = ? "
                + (StringUtils.isBlank(context.getContextParameter(FieldConstant.GRAY_NAME)) ? "" : "AND gray_name = ? ")
                + " AND nid > ? ORDER BY nid ", 1, 1);

        List<Object> paramList = CollectionUtils.list(
                context.getWhereParameter(FieldConstant.DATA_ID),
                context.getWhereParameter(FieldConstant.GROUP_ID),
                context.getWhereParameter(FieldConstant.TENANT_ID),
                context.getWhereParameter(FieldConstant.PUBLISH_TYPE),
                context.getWhereParameter(FieldConstant.NID));
        if (!StringUtils.isEmpty(context.getContextParameter(FieldConstant.GRAY_NAME))) {
            paramList.add(4, context.getWhereParameter(FieldConstant.GRAY_NAME));
        }
        return new MapperResult(sql, paramList);
    }
}
