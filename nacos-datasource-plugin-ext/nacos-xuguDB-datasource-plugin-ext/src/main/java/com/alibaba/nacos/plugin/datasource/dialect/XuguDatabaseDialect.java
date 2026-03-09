package com.alibaba.nacos.plugin.datasource.dialect;

import com.alibaba.nacos.plugin.datasource.emums.TrustedXuguFunctionEnum;
import com.alibaba.nacos.plugin.datasource.constants.DatabaseTypeConstant;

/**
 * xugu database dialect.
 *
 * @author jowee
 */
public class XuguDatabaseDialect extends AbstractDatabaseDialect {


    @Override
    public String getType() {
        return DatabaseTypeConstant.XUGU;
    }

    @Override
    public String getFunction(String functionName) {
        return TrustedXuguFunctionEnum.getFunctionByName(functionName);
    }
}
