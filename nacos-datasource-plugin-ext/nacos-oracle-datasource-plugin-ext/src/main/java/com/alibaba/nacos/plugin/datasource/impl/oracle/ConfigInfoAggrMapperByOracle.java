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
package com.alibaba.nacos.plugin.datasource.impl.oracle;

import java.util.ArrayList;
import java.util.List;

import com.alibaba.nacos.common.utils.CollectionUtils;
import com.alibaba.nacos.common.utils.NamespaceUtil;
import com.alibaba.nacos.plugin.datasource.constants.FieldConstant;
import com.alibaba.nacos.plugin.datasource.mapper.ConfigInfoAggrMapper;
import com.alibaba.nacos.plugin.datasource.model.MapperContext;
import com.alibaba.nacos.plugin.datasource.model.MapperResult;

/***
 * @author onewe
 */
public class ConfigInfoAggrMapperByOracle extends AbstractOracleMapper
		implements ConfigInfoAggrMapper {
	

	@Override
	public MapperResult findConfigInfoAggrByPageFetchRows(MapperContext context) {
		int startRow = context.getStartRow();
		int pageSize = context.getPageSize();
		String dataId = (String) context.getWhereParameter(FieldConstant.DATA_ID);
		String groupId = (String) context.getWhereParameter(FieldConstant.GROUP_ID);
		String tenantId = (String) context.getWhereParameter(FieldConstant.TENANT_ID);
		
		List<Object> sqlArgs = new ArrayList<>();
		sqlArgs.add(dataId);
		sqlArgs.add(groupId);
		sqlArgs.add(tenantId);
		
		String sqlBuilder =
				"SELECT data_id,group_id,tenant_id,datum_id,app_name,content FROM config_info_aggr WHERE data_id= ? AND "
						+ " group_id= ? " + " AND tenant_id = NVL(?, '"+ NamespaceUtil.getNamespaceDefaultId() +"') " + " ORDER BY datum_id ";
		String sql = getDatabaseDialect().getLimitPageSqlWithOffset(sqlBuilder, startRow, pageSize);
		return new MapperResult(sql, sqlArgs);
	}
	
	
	@Override
	public MapperResult batchRemoveAggr(MapperContext context) {
		final List<String> datumList = (List<String>) context.getWhereParameter(FieldConstant.DATUM_ID);
		final String dataId = (String) context.getWhereParameter(FieldConstant.DATA_ID);
		final String group = (String) context.getWhereParameter(FieldConstant.GROUP_ID);
		final String tenantTmp = (String) context.getWhereParameter(FieldConstant.TENANT_ID);
		
		List<Object> paramList = new ArrayList<>();
		paramList.add(dataId);
		paramList.add(group);
		paramList.add(tenantTmp);
		
		final StringBuilder placeholderString = new StringBuilder();
		for (int i = 0; i < datumList.size(); i++) {
			if (i != 0) {
				placeholderString.append(", ");
			}
			placeholderString.append('?');
			paramList.add(datumList.get(i));
		}
		
		String sql =
				"DELETE FROM config_info_aggr WHERE data_id = ? AND group_id = ? AND tenant_id = NVL(?, '"+NamespaceUtil.getNamespaceDefaultId()+"') AND datum_id IN ("
						+ placeholderString + ")";
		
		return new MapperResult(sql, paramList);
	}
	
	@Override
	public MapperResult aggrConfigInfoCount(MapperContext context) {
		final List<String> datumIds = (List<String>) context.getWhereParameter(FieldConstant.DATUM_ID);
		final Boolean isIn = (Boolean) context.getWhereParameter(FieldConstant.IS_IN);
		String dataId = (String) context.getWhereParameter(FieldConstant.DATA_ID);
		String group = (String) context.getWhereParameter(FieldConstant.GROUP_ID);
		String tenantTmp = (String) context.getWhereParameter(FieldConstant.TENANT_ID);
		
		List<Object> paramList = CollectionUtils.list(dataId, group, tenantTmp);
		
		StringBuilder sql = new StringBuilder(
				"SELECT count(*) FROM config_info_aggr WHERE data_id = ? AND group_id = ? AND tenant_id = NVL(?, '"+NamespaceUtil.getNamespaceDefaultId()+"') AND datum_id");
		if (isIn) {
			sql.append(" IN (");
		} else {
			sql.append(" NOT IN (");
		}
		for (int i = 0; i < datumIds.size(); i++) {
			if (i > 0) {
				sql.append(", ");
			}
			sql.append('?');
			paramList.add(datumIds.get(i));
		}
		sql.append(')');
		
		return new MapperResult(sql.toString(), paramList);
	}
	
	@Override
	public MapperResult findConfigInfoAggrIsOrdered(MapperContext context) {
		String dataId = (String) context.getWhereParameter(FieldConstant.DATA_ID);
		String groupId = (String) context.getWhereParameter(FieldConstant.GROUP_ID);
		String tenantId = (String) context.getWhereParameter(FieldConstant.TENANT_ID);
		
		String sql = "SELECT data_id,group_id,tenant_id,datum_id,app_name,content FROM "
				+ "config_info_aggr WHERE data_id = ? AND group_id = ? AND tenant_id = NVL(?, '"+NamespaceUtil.getNamespaceDefaultId()+"') ORDER BY datum_id";
		List<Object> paramList = CollectionUtils.list(dataId, groupId, tenantId);
		
		return new MapperResult(sql, paramList);
	}
}
