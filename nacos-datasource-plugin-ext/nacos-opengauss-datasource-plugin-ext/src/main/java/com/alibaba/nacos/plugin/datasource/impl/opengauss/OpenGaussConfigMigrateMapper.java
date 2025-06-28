package com.alibaba.nacos.plugin.datasource.impl.opengauss;

import com.alibaba.nacos.plugin.datasource.constants.DatabaseTypeConstant;
import com.alibaba.nacos.plugin.datasource.constants.PrimaryKeyConstant;
import com.alibaba.nacos.plugin.datasource.impl.base.BaseConfigMigrateMapper;

public class OpenGaussConfigMigrateMapper extends BaseConfigMigrateMapper {
    @Override
    public String getDataSource() {
        return DatabaseTypeConstant.GUASSDB;
    }

    @Override
    public String[] getPrimaryKeyGeneratedKeys() {
        return PrimaryKeyConstant.UPPER_RETURN_PRIMARY_KEYS;
    }

}
