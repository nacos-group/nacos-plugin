package com.alibaba.nacos.plugin.datasource.dialect;

import com.alibaba.nacos.plugin.datasource.constants.DatabaseTypeConstant;
import com.alibaba.nacos.plugin.datasource.enums.TrustedKingbaseFunctionEnum;

/**
 * kingbase database dialect.
 *
 * @author leon
 * &#064;date  2024-09-09 15:37:28
 */
public class KingbaseDatabaseDialect extends AbstractDatabaseDialect {

    @Override
    public String getType() {
        return DatabaseTypeConstant.KINGBASE;
    }

    @Override
    public String getFunction(String functionName) {
        return TrustedKingbaseFunctionEnum.getFunctionByName(functionName);
    }
}
