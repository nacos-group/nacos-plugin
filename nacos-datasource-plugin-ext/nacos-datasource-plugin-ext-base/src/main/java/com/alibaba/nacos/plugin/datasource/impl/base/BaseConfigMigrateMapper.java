package com.alibaba.nacos.plugin.datasource.impl.base;

import com.alibaba.nacos.plugin.datasource.constants.TableConstant;
import com.alibaba.nacos.plugin.datasource.dialect.DatabaseDialect;
import com.alibaba.nacos.plugin.datasource.impl.mysql.ConfigMigrateMapperByMysql;
import com.alibaba.nacos.plugin.datasource.manager.DatabaseDialectManager;

public class BaseConfigMigrateMapper extends ConfigMigrateMapperByMysql {
    private final DatabaseDialect databaseDialect;

    public BaseConfigMigrateMapper() {
        databaseDialect = DatabaseDialectManager.getInstance().getDialect(getDataSource());
    }

    @Override
    public String getTableName() {
        return TableConstant.MIGRATE_CONFIG;
    }

    @Override
    public String getFunction(String functionName) {
        return databaseDialect.getFunction(functionName);
    }
}
