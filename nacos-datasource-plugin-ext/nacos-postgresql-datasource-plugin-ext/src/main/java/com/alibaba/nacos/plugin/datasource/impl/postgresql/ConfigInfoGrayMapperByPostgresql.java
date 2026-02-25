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

package com.alibaba.nacos.plugin.datasource.impl.postgresql;

import com.alibaba.nacos.common.utils.CollectionUtils;
import com.alibaba.nacos.plugin.datasource.mapper.ConfigInfoGrayMapper;
import com.alibaba.nacos.plugin.datasource.model.MapperContext;
import com.alibaba.nacos.plugin.datasource.model.MapperResult;

/**
 * The postgresql implementation of ConfigInfoGrayMapper.
 *
 * @author Ken
 **/
public class ConfigInfoGrayMapperByPostgresql extends AbstractMapperByPostgresql implements ConfigInfoGrayMapper {
    
    private String getLimitPageSqlWithMark(String sql) {
        return getDatabaseDialect().getLimitPageSqlWithMark(sql);
    }
    
    /**
     * {@inheritDoc}
     */
    @Override
    public MapperResult findAllConfigInfoGrayForDumpAllFetchRows(MapperContext context) {
        int startRow = context.getStartRow();
        int pageSize = context.getPageSize();
        String sqlInner = getLimitPageSqlWithMark("SELECT id FROM config_info_gray  ORDER BY id ");
        String sql = " SELECT t.id,data_id,group_id,tenant_id,gray_name,app_name,content,md5,gmt_modified " + " FROM ( "
                + sqlInner + "  )  g," + " config_info_gray t WHERE g.id = t.id ";
        return new MapperResult(sql, CollectionUtils.list(startRow, pageSize));
    }
}
