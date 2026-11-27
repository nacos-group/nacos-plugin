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

package com.alibaba.nacos.plugin.datasource.impl.dm;

import com.alibaba.nacos.plugin.datasource.constants.DatabaseTypeConstant;
import com.alibaba.nacos.plugin.datasource.constants.PrimaryKeyConstant;
import com.alibaba.nacos.plugin.datasource.impl.base.BaseGroupCapacityMapper;
import com.alibaba.nacos.plugin.datasource.model.MapperContext;
import com.alibaba.nacos.plugin.datasource.model.MapperResult;

/**
 * The base implementation of GroupCapacityMapper.
 *
 * @author Xiao Yong
 **/
public class GroupCapacityMapperByDaMeng extends BaseGroupCapacityMapper {

    @Override
    public String getDataSource() {
        return DatabaseTypeConstant.DM;
    }

    @Override
    public String[] getPrimaryKeyGeneratedKeys() {
        return PrimaryKeyConstant.UPPER_RETURN_PRIMARY_KEYS;
    }

    @Override
    public MapperResult select(MapperContext context) {
        return DaMengCapacitySql.unquoteUsage(super.select(context));
    }

    @Override
    public MapperResult insertIntoSelect(MapperContext context) {
        return DaMengCapacitySql.unquoteUsage(super.insertIntoSelect(context));
    }

    @Override
    public MapperResult insertIntoSelectByWhere(MapperContext context) {
        return DaMengCapacitySql.unquoteUsage(super.insertIntoSelectByWhere(context));
    }

    @Override
    public MapperResult incrementUsageByWhereQuotaEqualZero(MapperContext context) {
        return DaMengCapacitySql.unquoteUsage(super.incrementUsageByWhereQuotaEqualZero(context));
    }

    @Override
    public MapperResult incrementUsageByWhereQuotaNotEqualZero(MapperContext context) {
        return DaMengCapacitySql.unquoteUsage(super.incrementUsageByWhereQuotaNotEqualZero(context));
    }

    @Override
    public MapperResult incrementUsageByWhere(MapperContext context) {
        return DaMengCapacitySql.unquoteUsage(super.incrementUsageByWhere(context));
    }

    @Override
    public MapperResult decrementUsageByWhere(MapperContext context) {
        return DaMengCapacitySql.unquoteUsage(super.decrementUsageByWhere(context));
    }

    @Override
    public MapperResult updateUsage(MapperContext context) {
        return DaMengCapacitySql.unquoteUsage(super.updateUsage(context));
    }

    @Override
    public MapperResult updateUsageByWhere(MapperContext context) {
        return DaMengCapacitySql.unquoteUsage(super.updateUsageByWhere(context));
    }
}
