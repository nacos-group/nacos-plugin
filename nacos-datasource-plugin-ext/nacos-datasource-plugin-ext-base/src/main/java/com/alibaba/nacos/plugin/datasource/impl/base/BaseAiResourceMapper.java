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

import com.alibaba.nacos.plugin.datasource.constants.FieldConstant;
import com.alibaba.nacos.plugin.datasource.constants.TableConstant;
import com.alibaba.nacos.plugin.datasource.dialect.DatabaseDialect;
import com.alibaba.nacos.plugin.datasource.manager.DatabaseDialectManager;
import com.alibaba.nacos.plugin.datasource.mapper.AbstractMapper;
import com.alibaba.nacos.plugin.datasource.mapper.AiResourceMapper;
import com.alibaba.nacos.plugin.datasource.mapper.ext.WhereBuilder;
import com.alibaba.nacos.plugin.datasource.model.MapperContext;
import com.alibaba.nacos.plugin.datasource.model.MapperResult;

import java.util.ArrayList;
import java.util.List;

/**
 * @author Ken
 */
public abstract class BaseAiResourceMapper extends AbstractMapper implements AiResourceMapper {
    private DatabaseDialect databaseDialect;
    
    public BaseAiResourceMapper() {
        databaseDialect = DatabaseDialectManager.getInstance().getDialect(getDataSource());
    }
    
    @Override
    public MapperResult findAiResourceFetchRows(MapperContext context) {
        WhereBuilder where = new WhereBuilder(
                "select id,gmt_create,gmt_modified,name,type,c_desc,status,namespace_id,"
                        + "biz_tags,ext,c_from,version_info,meta_version,scope,owner,download_count"
                        + " from ai_resource");
        
        where.eq("namespace_id", context.getWhereParameter(FieldConstant.NAMESPACE_ID));
        
        MapperResult build = where.build();
        String sql = getLimitPageSqlWithOffset(build.getSql() + resolveOrderByClause(context), context.getStartRow(),
                context.getPageSize());
        List<Object> params = new ArrayList<>(build.getParamList());
        params.add(context.getStartRow());
        params.add(context.getPageSize());
        return new MapperResult(sql, params);
    }
    
    @Override
    public String getTableName() {
        return TableConstant.AI_RESOURCE;
    }
    
    public String getLimitPageSqlWithOffset(String sql, int startRow, int pageSize) {
        return databaseDialect.getLimitPageSqlWithOffset(sql, startRow, pageSize);
    }
    
    @Override
    public String getFunction(String functionName) {
        return databaseDialect.getFunction(functionName);
    }
    
}
