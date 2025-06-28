package com.alibaba.nacos.plugin.datasource.impl.oracle;

import com.alibaba.nacos.plugin.datasource.constants.DatabaseTypeConstant;
import com.alibaba.nacos.plugin.datasource.impl.base.BaseConfigMigrateMapper;

public class ConfigMigrateMapperByOracle extends BaseConfigMigrateMapper {
    @Override
    public String getDataSource() {
        return DatabaseTypeConstant.ORACLE;
    }

}
