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
import com.alibaba.nacos.plugin.datasource.constants.TableConstant;
import com.alibaba.nacos.plugin.datasource.dialect.DatabaseDialect;
import com.alibaba.nacos.plugin.datasource.impl.mysql.ConfigInfoGrayMapperByMySql;
import com.alibaba.nacos.plugin.datasource.manager.DatabaseDialectManager;
import com.alibaba.nacos.plugin.datasource.model.MapperContext;
import com.alibaba.nacos.plugin.datasource.model.MapperResult;

import java.util.Collections;
import java.util.List;

/**
 * The base implementation of ConfigTagsRelationMapper.
 *
 * @author Long Yu
 **/
public class BaseConfigInfoGrayMapper extends ConfigInfoGrayMapperByMySql {

    private final DatabaseDialect databaseDialect;

    public BaseConfigInfoGrayMapper() {
        databaseDialect = DatabaseDialectManager.getInstance().getDialect(getDataSource());
    }

    @Override
    public String getTableName() {
        return TableConstant.CONFIG_INFO_GRAY;
    }

    @Override
    public MapperResult findAllConfigInfoGrayForDumpAllFetchRows(MapperContext context) {
        String sql = databaseDialect.getLimitPageSqlWithOffset(
                " SELECT id,data_id,group_id,tenant_id,gray_name,gray_rule,app_name,content,md5,gmt_modified "
                        + " FROM  config_info_gray  ORDER BY id", context.getStartRow(), context.getPageSize());
        return new MapperResult(sql, Collections.emptyList());
    }

    @Override
    public String getFunction(String functionName) {
        return databaseDialect.getFunction(functionName);
    }
}
