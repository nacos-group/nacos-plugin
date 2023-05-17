/*
 * Copyright 1999-2018 Alibaba Group Holding Ltd.
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
package com.alibaba.nacos.plugin.datasource.impl.oracle;

import java.util.List;

import com.alibaba.nacos.common.utils.NamespaceUtil;
import com.alibaba.nacos.common.utils.StringUtils;
import com.alibaba.nacos.plugin.datasource.constants.DatabaseTypeConstant;
import com.alibaba.nacos.plugin.datasource.dialect.DatabaseDialect;
import com.alibaba.nacos.plugin.datasource.manager.DatabaseDialectManager;
import com.alibaba.nacos.plugin.datasource.mapper.AbstractMapper;

/**
 * @author onewe
 */
public abstract class AbstractOracleMapper extends AbstractMapper {

	private final DatabaseDialect databaseDialect;

	public AbstractOracleMapper() {
		databaseDialect = DatabaseDialectManager.getInstance()
				.getDialect(getDataSource());
	}

	@Override
	public String getDataSource() {
		return DatabaseTypeConstant.ORACLE;
	}

	@Override
	public String select(List<String> columns, List<String> where) {
		StringBuilder sql = new StringBuilder();
		String method = "SELECT ";
		sql.append(method);
		for (int i = 0; i < columns.size(); i++) {
			sql.append(columns.get(i));
			if (i == columns.size() - 1) {
				sql.append(" ");
			}
			else {
				sql.append(",");
			}
		}
		sql.append("FROM ");
		sql.append(getTableName());
		sql.append(" ");

		if (where.size() == 0) {
			return sql.toString();
		}

		sql.append("WHERE ");
		for (int i = 0; i < where.size(); i++) {
			String condition = where.get(i);
			if (StringUtils.equalsIgnoreCase(condition, "tenant_id")) {
				sql.append("tenant_id").append(" = ").append("NVL(?, '").append(NamespaceUtil.getNamespaceDefaultId())
						.append("')");
			}
			else {
				sql.append(condition).append(" = ").append("?");
			}

			if (i != where.size() - 1) {
				sql.append(" AND ");
			}
		}
		return sql.toString();
	}

	@Override
	public String update(List<String> columns, List<String> where) {
		StringBuilder sql = new StringBuilder();
		String method = "UPDATE ";
		sql.append(method);
		sql.append(getTableName()).append(" ").append("SET ");

		for (int i = 0; i < columns.size(); i++) {
			sql.append(columns.get(i)).append(" = ").append("?");
			if (i != columns.size() - 1) {
				sql.append(",");
			}
		}

		if (where.size() == 0) {
			return sql.toString();
		}

		sql.append(" WHERE ");

		for (int i = 0; i < where.size(); i++) {
			String condition = where.get(i);
			if (StringUtils.equalsIgnoreCase(condition, "tenant_id")) {
				sql.append("tenant_id").append(" = ").append("NVL(?, '").append(NamespaceUtil.getNamespaceDefaultId())
						.append("')");
			}
			else {
				sql.append(condition).append(" = ").append("?");
			}
			if (i != where.size() - 1) {
				sql.append(" AND ");
			}
		}
		return sql.toString();
	}

	@Override
	public String delete(List<String> params) {
		StringBuilder sql = new StringBuilder();
		String method = "DELETE ";
		sql.append(method).append("FROM ").append(getTableName()).append(" ")
				.append("WHERE ");
		for (int i = 0; i < params.size(); i++) {

			String condition = params.get(i);
			if (StringUtils.equalsIgnoreCase(condition, "tenant_id")) {
				sql.append("tenant_id").append(" = ").append("NVL(?, '").append(NamespaceUtil.getNamespaceDefaultId())
						.append("')");
			}
			else {
				sql.append(condition).append(" = ").append("?");
			}

			if (i != params.size() - 1) {
				sql.append("AND ");
			}
		}

		return sql.toString();
	}

	@Override
	public String count(List<String> where) {
		StringBuilder sql = new StringBuilder();
		String method = "SELECT ";
		sql.append(method);
		sql.append("COUNT(*) FROM ");
		sql.append(getTableName());
		sql.append(" ");

		if (null == where || where.size() == 0) {
			return sql.toString();
		}

		sql.append("WHERE ");
		for (int i = 0; i < where.size(); i++) {
			String condition = where.get(i);
			if (StringUtils.equalsIgnoreCase(condition, "tenant_id")) {
				sql.append("tenant_id").append(" = ").append("NVL(?, '").append(NamespaceUtil.getNamespaceDefaultId())
						.append("')");
			}
			else {
				sql.append(condition).append(" = ").append("?");
			}
			if (i != where.size() - 1) {
				sql.append(" AND ");
			}
		}
		return sql.toString();
	}

	protected DatabaseDialect getDatabaseDialect() {
		return databaseDialect;
	}
}
