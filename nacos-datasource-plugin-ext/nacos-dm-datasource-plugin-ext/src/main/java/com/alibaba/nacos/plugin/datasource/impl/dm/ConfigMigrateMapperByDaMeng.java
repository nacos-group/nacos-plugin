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

import com.alibaba.nacos.common.utils.CollectionUtils;
import com.alibaba.nacos.common.utils.StringUtils;
import com.alibaba.nacos.plugin.datasource.constants.DatabaseTypeConstant;
import com.alibaba.nacos.plugin.datasource.constants.FieldConstant;
import com.alibaba.nacos.plugin.datasource.constants.PrimaryKeyConstant;
import com.alibaba.nacos.plugin.datasource.mapper.ConfigMigrateMapper;
import com.alibaba.nacos.plugin.datasource.model.MapperContext;
import com.alibaba.nacos.plugin.datasource.model.MapperResult;

import java.util.ArrayList;
import java.util.List;

/**
 * @author Ken
 */
public class ConfigMigrateMapperByDaMeng extends AbstractMapperByDaMeng implements ConfigMigrateMapper {
    
    @Override
    public MapperResult getConfigConflictCount(MapperContext context) {
        String sql = "SELECT COUNT(*) FROM config_info ci1"
                + " WHERE ci1.tenant_id = 'public' AND (ci1.src_user <> ? OR ci1.src_user IS NULL) "
                + " AND EXISTS (SELECT 1 FROM config_info ci2"
                + " WHERE ci2.data_id = ci1.data_id AND ci2.group_id = ci1.group_id AND ci2.md5 <> ci1.md5"
                + " AND ci2.tenant_id = '' AND (ci2.src_user <> ? OR ci2.src_user IS NULL))";
        Object srcUser = context.getWhereParameter(FieldConstant.SRC_USER);
        return new MapperResult(sql, CollectionUtils.list(srcUser, srcUser));
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
