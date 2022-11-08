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

import com.alibaba.nacos.plugin.datasource.dialect.DatabaseDialect;
import com.alibaba.nacos.plugin.datasource.impl.mysql.TenantCapacityMapperByMySql;
import com.alibaba.nacos.plugin.datasource.manager.DatabaseDialectManager;

/**
 * The base implementation of TenantCapacityMapper.
 *
 * @author Long Yu
 **/
public class BaseTenantCapacityMapper extends TenantCapacityMapperByMySql {
    
    private DatabaseDialect databaseDialect;
    
    public BaseTenantCapacityMapper() {
        databaseDialect = DatabaseDialectManager.getInstance().getDialect(getDataSource());
    }
    
    @Override
    public String getCapacityList4CorrectUsage() {
        return databaseDialect.getLimitTopSqlWithMark("SELECT id, tenant_id FROM tenant_capacity WHERE id>?");
    }

}
