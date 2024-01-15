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

import com.alibaba.nacos.plugin.datasource.manager.DatabaseDialectManager;
import com.alibaba.nacos.plugin.datasource.mapper.AbstractMapper;
import com.alibaba.nacos.plugin.datasource.mapper.ConfigInfoTagMapper;
import com.alibaba.nacos.plugin.datasource.model.MapperContext;
import com.alibaba.nacos.plugin.datasource.model.MapperResult;

import java.util.Collections;

/**
 * The base implementation of ConfigTagsRelationMapper.
 *
 * @author Long Yu
 **/
public abstract class BaseConfigInfoTagMapper extends AbstractMapper implements ConfigInfoTagMapper {

    @Override
    public MapperResult findAllConfigInfoTagForDumpAllFetchRows(MapperContext context) {
        int startRow = context.getStartRow();
        int pageSize = context.getPageSize();
        String innerSql = DatabaseDialectManager.getInstance().getDialect(getDataSource())
                .getLimitPageSqlWithOffset("SELECT id FROM config_info_tag  ORDER BY id ", startRow, pageSize);
        String sql = " SELECT t.id,data_id,group_id,tenant_id,tag_id,app_name,content,md5,gmt_modified " + " FROM (  "
                + innerSql + "  ) " + "g, config_info_tag t  WHERE g.id = t.id  ";
        return new MapperResult(sql, Collections.emptyList());
    }
    
}
