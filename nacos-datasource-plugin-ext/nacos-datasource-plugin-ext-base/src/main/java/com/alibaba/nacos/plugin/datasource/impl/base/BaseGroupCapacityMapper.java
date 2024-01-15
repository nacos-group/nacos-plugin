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
import com.alibaba.nacos.plugin.datasource.constants.FieldConstant;
import com.alibaba.nacos.plugin.datasource.manager.DatabaseDialectManager;
import com.alibaba.nacos.plugin.datasource.mapper.AbstractMapper;
import com.alibaba.nacos.plugin.datasource.mapper.GroupCapacityMapper;
import com.alibaba.nacos.plugin.datasource.model.MapperContext;
import com.alibaba.nacos.plugin.datasource.model.MapperResult;

/**
 * The base implementation of GroupCapacityMapper.
 *
 * @author Long Yu
 **/
public abstract class BaseGroupCapacityMapper extends AbstractMapper implements GroupCapacityMapper {

    @Override
    public MapperResult selectGroupInfoBySize(MapperContext context) {
        String sql = DatabaseDialectManager.getInstance().getDialect(getDataSource()).getLimitTopSqlWithMark("SELECT id, group_id FROM group_capacity WHERE id > ?");
        return new MapperResult(sql,
                CollectionUtils.list(context.getWhereParameter(FieldConstant.ID), context.getPageSize()));
    }
    
}
