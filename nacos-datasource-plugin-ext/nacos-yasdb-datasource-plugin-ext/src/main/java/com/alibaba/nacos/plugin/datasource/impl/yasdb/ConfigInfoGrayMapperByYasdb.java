/*
 * Copyright 1999-2023 Alibaba Group Holding Ltd.
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
package com.alibaba.nacos.plugin.datasource.impl.yasdb;

import com.alibaba.nacos.plugin.datasource.constants.TableConstant;
import com.alibaba.nacos.plugin.datasource.mapper.ConfigInfoGrayMapper;
import com.alibaba.nacos.plugin.datasource.model.MapperContext;
import com.alibaba.nacos.plugin.datasource.model.MapperResult;

import java.util.Collections;

/**
 * YASDB implementation of ConfigInfoGrayMapper.
 */
public class ConfigInfoGrayMapperByYasdb extends AbstractYasdbMapper implements ConfigInfoGrayMapper {

    @Override
    public String getTableName() {
        return TableConstant.CONFIG_INFO_GRAY;
    }

    @Override
    public MapperResult findAllConfigInfoGrayForDumpAllFetchRows(MapperContext context) {
        int startRow = context.getStartRow();
        int pageSize = context.getPageSize();
        String sqlBuilder = " SELECT id,data_id,group_id,tenant_id,gray_name,gray_rule,app_name,content,md5,gmt_modified "
                + " FROM config_info_gray ORDER BY id ";
        String sql = getDatabaseDialect().getLimitPageSqlWithOffset(sqlBuilder, startRow, pageSize);
        return new MapperResult(sql, Collections.emptyList());
    }
}
