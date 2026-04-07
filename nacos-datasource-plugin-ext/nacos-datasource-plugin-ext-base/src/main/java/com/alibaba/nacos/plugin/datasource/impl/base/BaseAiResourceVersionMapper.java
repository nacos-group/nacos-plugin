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

package com.alibaba.nacos.plugin.datasource.impl.base;

import com.alibaba.nacos.common.utils.StringUtils;
import com.alibaba.nacos.plugin.datasource.constants.FieldConstant;
import com.alibaba.nacos.plugin.datasource.constants.TableConstant;
import com.alibaba.nacos.plugin.datasource.dialect.DatabaseDialect;
import com.alibaba.nacos.plugin.datasource.manager.DatabaseDialectManager;
import com.alibaba.nacos.plugin.datasource.mapper.AbstractMapper;
import com.alibaba.nacos.plugin.datasource.mapper.AiResourceMapper;
import com.alibaba.nacos.plugin.datasource.mapper.AiResourceVersionMapper;
import com.alibaba.nacos.plugin.datasource.mapper.ext.WhereBuilder;
import com.alibaba.nacos.plugin.datasource.model.MapperContext;
import com.alibaba.nacos.plugin.datasource.model.MapperResult;

import java.util.ArrayList;
import java.util.List;

/**
 * @author Ken
 */
public abstract class BaseAiResourceVersionMapper extends AbstractMapper implements AiResourceVersionMapper {
    private DatabaseDialect databaseDialect;
    
    public BaseAiResourceVersionMapper() {
        databaseDialect = DatabaseDialectManager.getInstance().getDialect(getDataSource());
    }
    
    @Override
    public MapperResult findAiResourceVersionFetchRows(MapperContext context) {
        WhereBuilder where = new WhereBuilder(
                "select id,gmt_create,gmt_modified,type,author,name,c_desc,status,version,namespace_id,"
                        + "storage,publish_pipeline_info,download_count "
                        + " from ai_resource_version");
        where.eq("namespace_id", context.getWhereParameter(FieldConstant.NAMESPACE_ID));
        where.and().eq("name",context.getWhereParameter(FieldConstant.NAME));
        
        Object type = context.getWhereParameter(FieldConstant.TYPE);
        if (type != null && StringUtils.isNotBlank(String.valueOf(type))) {
            where.and().eq("type", type);
        }

        Object status = context.getWhereParameter(FieldConstant.STATUS);
        if (status != null && StringUtils.isNotBlank(String.valueOf(status))) {
            where.and().eq("status", status);
        }

        Object version = context.getWhereParameter(FieldConstant.VERSION);
        if (version != null && StringUtils.isNotBlank(String.valueOf(version))) {
            where.and().eq("version", version);
        }
        
        MapperResult built = where.build();
        String sql = built.getSql() + " ORDER BY gmt_modified DESC LIMIT ?,?";
        List<Object> params = new ArrayList<>(built.getParamList());
        params.add(context.getStartRow());
        params.add(context.getPageSize());
        return new MapperResult(sql, params);
    }
    
    @Override
    public String getTableName() {
        return TableConstant.AI_RESOURCE_VERSION;
    }
    
    public String getLimitPageSqlWithOffset(String sql, int startRow, int pageSize) {
        return databaseDialect.getLimitPageSqlWithOffset(sql, startRow, pageSize);
    }
    
    @Override
    public String getFunction(String functionName) {
        return databaseDialect.getFunction(functionName);
    }
    
}
