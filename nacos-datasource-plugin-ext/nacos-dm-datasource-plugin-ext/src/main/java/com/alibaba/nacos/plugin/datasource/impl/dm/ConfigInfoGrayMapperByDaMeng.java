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
import com.alibaba.nacos.plugin.datasource.constants.PrimaryKeyConstant;
import com.alibaba.nacos.plugin.datasource.mapper.ConfigInfoGrayMapper;
import com.alibaba.nacos.plugin.datasource.model.MapperContext;
import com.alibaba.nacos.plugin.datasource.model.MapperResult;

import java.util.Collections;

/**
 * @author Ken
 */
public class ConfigInfoGrayMapperByDaMeng extends AbstractMapperByDaMeng implements ConfigInfoGrayMapper {

    @Override
    public MapperResult findAllConfigInfoGrayForDumpAllFetchRows(MapperContext context) {
        String sql = getLimitPageSqlWithOffset("SELECT id,data_id,group_id,tenant_id,gray_name,app_name,content,md5,gmt_modified "
                        +" from config_info_gray ORDER BY id ", context.getStartRow(), context.getPageSize());
        return new MapperResult(sql, Collections.emptyList());
    }
    
    private String getLimitPageSqlWithOffset(String sql, int offset, int limit) {
        return getDialect().getLimitPageSqlWithOffset(sql,offset,limit);
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
