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

package com.alibaba.nacos.plugin.datasource.impl.kingbase;

import com.alibaba.nacos.plugin.datasource.constants.DatabaseTypeConstant;
import com.alibaba.nacos.plugin.datasource.dialect.DatabaseDialect;
import com.alibaba.nacos.plugin.datasource.enums.kingbase.TrustedKingbaseFunctionEnum;
import com.alibaba.nacos.plugin.datasource.manager.DatabaseDialectManager;
import com.alibaba.nacos.plugin.datasource.mapper.AbstractMapper;

/**
 * @author 619008336
 * @description The abstract Kingbase mapper contains CRUD methods.
 * @date 2026/01/12
 */
public abstract class AbstractMapperByKingbase extends AbstractMapper {
    
    private volatile DatabaseDialect databaseDialect;
    
    public DatabaseDialect getDatabaseDialect() {
        if (databaseDialect == null) {
            synchronized (this) {
                if (databaseDialect == null) {
                    databaseDialect = DatabaseDialectManager.getInstance().getDialect(getDataSource());
                }
            }
        }
        return databaseDialect;
    }
    
    @Override
    public String getDataSource() {
        return DatabaseTypeConstant.KINGBASE;
    }
    
    @Override
    public String getFunction(String functionName) {
        return TrustedKingbaseFunctionEnum.getFunctionByName(functionName);
    }
}
