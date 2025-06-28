package com.alibaba.nacos.plugin.datasource.impl.postgresql;

import com.alibaba.nacos.plugin.datasource.constants.DatabaseTypeConstant;
import com.alibaba.nacos.plugin.datasource.impl.base.BaseConfigMigrateMapper;

public class ConfigMigrateMapperByPostgresql extends BaseConfigMigrateMapper {
    @Override
    public String getDataSource() {
        return DatabaseTypeConstant.POSTGRESQL;
    }

}
