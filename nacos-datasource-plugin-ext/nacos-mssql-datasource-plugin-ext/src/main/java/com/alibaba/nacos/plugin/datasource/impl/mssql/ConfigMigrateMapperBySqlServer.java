package com.alibaba.nacos.plugin.datasource.impl.mssql;

import com.alibaba.nacos.plugin.datasource.constants.DatabaseTypeConstant;
import com.alibaba.nacos.plugin.datasource.impl.base.BaseConfigMigrateMapper;

public class ConfigMigrateMapperBySqlServer extends BaseConfigMigrateMapper {
    @Override
    public String getDataSource() {
        return DatabaseTypeConstant.SQLSERVER;
    }

}
