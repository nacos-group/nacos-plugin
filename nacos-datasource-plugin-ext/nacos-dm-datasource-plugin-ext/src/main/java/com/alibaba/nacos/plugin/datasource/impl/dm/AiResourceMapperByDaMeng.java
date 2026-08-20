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

package com.alibaba.nacos.plugin.datasource.impl.dm;

import com.alibaba.nacos.plugin.datasource.constants.DatabaseTypeConstant;
import com.alibaba.nacos.plugin.datasource.constants.FieldConstant;
import com.alibaba.nacos.plugin.datasource.constants.PrimaryKeyConstant;
import com.alibaba.nacos.plugin.datasource.mapper.AiResourceMapper;
import com.alibaba.nacos.plugin.datasource.mapper.ext.WhereBuilder;
import com.alibaba.nacos.plugin.datasource.model.MapperContext;
import com.alibaba.nacos.plugin.datasource.model.MapperResult;

import java.util.ArrayList;
import java.util.List;

/**
 * @author Ken
 */
public class AiResourceMapperByDaMeng extends AbstractMapperByDaMeng implements AiResourceMapper {
    
    @Override
    public MapperResult findAiResourceFetchRows(MapperContext context) {
        WhereBuilder where = new WhereBuilder("select id,gmt_create,gmt_modified,name,type,c_desc,status,namespace_id,"
                + "biz_tags,ext,c_from,version_info,meta_version,scope,owner,download_count from ai_resource");
        
        where.eq("namespace_id", context.getWhereParameter(FieldConstant.NAMESPACE_ID));
        
        MapperResult build = where.build();
        String sql = getLimitPageSqlWithMark(build.getSql() + resolveOrderByClause(context));
        List<Object> params = new ArrayList<>(build.getParamList());
        params.add(context.getPageSize());
        params.add(context.getStartRow());
        return new MapperResult(sql, params);
    }
    
    private String getLimitPageSqlWithMark(String sql) {
        return getDialect().getLimitPageSqlWithMark(sql);
    }
    
    @Override
    public String getDataSource() {
        return DatabaseTypeConstant.DM;
    }
    
    @Override
    public String[] getPrimaryKeyGeneratedKeys() {
        return PrimaryKeyConstant.UPPER_RETURN_PRIMARY_KEYS;
    }
}
