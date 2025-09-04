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
import com.alibaba.nacos.plugin.datasource.dialect.DatabaseDialect;
import com.alibaba.nacos.plugin.datasource.manager.DatabaseDialectManager;
import com.alibaba.nacos.plugin.datasource.mapper.AbstractMapper;
import com.alibaba.nacos.plugin.datasource.mapper.HistoryConfigInfoMapper;
import com.alibaba.nacos.plugin.datasource.mapper.TenantCapacityMapper;
import com.alibaba.nacos.plugin.datasource.model.MapperContext;
import com.alibaba.nacos.plugin.datasource.model.MapperResult;

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
    public MapperResult removeConfigHistory(MapperContext context) {
        return null;
    }

    @Override
    public MapperResult pageFindConfigHistoryFetchRows(MapperContext context) {
        return null;
    }

    @Override
    public String getFunction(String functionName) {
        return databaseDialect.getFunction(functionName);
    }

    @Override
    public MapperResult findConfigHistoryCountByTime(MapperContext context) {
        return HistoryConfigInfoMapper.super.findConfigHistoryCountByTime(context);
    }

    @Override
    public MapperResult findDeletedConfig(MapperContext context) {
        return HistoryConfigInfoMapper.super.findDeletedConfig(context);
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
        return HistoryConfigInfoMapper.super.getNextHistoryInfo(context);
    }
}
