package com.alibaba.nacos.plugin.datasource.dialect;

import com.alibaba.nacos.plugin.datasource.constants.DatabaseTypeConstant;
import com.alibaba.nacos.plugin.datasource.enums.kingbase.TrustedKingbaseFunctionEnum;

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
    
    @Override
    public String getLimitPageSqlWithMark(String sql) {
        return sql + "  LIMIT ? OFFSET ? ";
    }

    @Override
    public String getLimitPageSql(String sql, int pageNo, int pageSize) {
        return sql + " LIMIT " + pageSize + "  OFFSET " + getPagePrevNum(pageNo, pageSize);
    }

    @Override
    public String getLimitPageSqlWithOffset(String sql, int startOffset, int pageSize) {
        return sql + " LIMIT " + pageSize + "  OFFSET " + startOffset;
    }
}
