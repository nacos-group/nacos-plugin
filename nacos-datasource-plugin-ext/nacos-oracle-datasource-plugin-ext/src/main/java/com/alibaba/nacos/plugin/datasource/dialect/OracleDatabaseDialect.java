/*
 * Copyright 1999-2023 Alibaba Group Holding Ltd.
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

package com.alibaba.nacos.plugin.datasource.dialect;

import com.alibaba.nacos.common.utils.NamespaceUtil;
import com.alibaba.nacos.plugin.datasource.constants.DatabaseTypeConstant;
import com.alibaba.nacos.plugin.datasource.enums.TrustedOracleFunctionEnum;

/***
 * oracle datasource dialect.
 * @author onewe
 */
public class OracleDatabaseDialect extends AbstractDatabaseDialect {

	private static final String DEFAULT_NAMESPACE_ID = "PUBLIC";

	static {
		NamespaceUtil.namespaceDefaultId = DEFAULT_NAMESPACE_ID;
	}

	@Override
	public String getType() {
		return DatabaseTypeConstant.ORACLE;
	}

	@Override
	public String getLimitTopSqlWithMark(String sql) {
		// 使用Oracle 11g兼容的ROWNUM方式实现
		return "SELECT * FROM (" + sql + ") WHERE ROWNUM <= ?";
	}

	@Override
	public String getLimitPageSqlWithMark(String sql) {
		// 使用Oracle 11g兼容的分页方式实现
		return "SELECT * FROM (SELECT ROWNUM rn, t.* FROM (" + sql + ") t WHERE ROWNUM <= ?) WHERE rn > ?";
	}

	@Override
	public String getLimitPageSqlWithOffset(String sql, int startOffset, int pageSize) {
		int endOffset = startOffset + pageSize;
		// 使用Oracle 11g兼容的分页方式实现
		return "SELECT * FROM (SELECT ROWNUM rn, t.* FROM (" + sql + ") t WHERE ROWNUM <= " + endOffset + ") WHERE rn > " + startOffset;
	}

	@Override
	public String getLimitPageSql(String sql, int pageNo, int pageSize) {
		int startOffset = getPagePrevNum(pageNo, pageSize);
		int endOffset = startOffset + pageSize;
		// 使用Oracle 11g兼容的分页方式实现
		return "SELECT * FROM (SELECT ROWNUM rn, t.* FROM (" + sql + ") t WHERE ROWNUM <= " + endOffset + ") WHERE rn > " + startOffset;
	}


	@Override
	public String getFunction(String functionName) {
		return TrustedOracleFunctionEnum.getFunctionByName(functionName);
	}
}
