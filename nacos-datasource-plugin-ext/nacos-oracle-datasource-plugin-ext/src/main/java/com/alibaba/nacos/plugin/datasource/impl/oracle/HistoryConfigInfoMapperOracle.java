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

import com.alibaba.nacos.common.utils.CollectionUtils;
import com.alibaba.nacos.common.utils.NamespaceUtil;
import com.alibaba.nacos.plugin.datasource.constants.FieldConstant;
import com.alibaba.nacos.plugin.datasource.mapper.HistoryConfigInfoMapper;
import com.alibaba.nacos.plugin.datasource.model.MapperContext;
import com.alibaba.nacos.plugin.datasource.model.MapperResult;

import java.util.ArrayList;
import java.util.List;

/***
 * @author onewe
 */
public class HistoryConfigInfoMapperOracle extends AbstractOracleMapper
		implements HistoryConfigInfoMapper {

	@Override
	public MapperResult removeConfigHistory(MapperContext context) {
		String sql = "DELETE FROM his_config_info WHERE ROWID in (SELECT ROWID FROM his_config_info WHERE gmt_modified < ? FETCH FIRST ? ROWS ONLY) ";
		return new MapperResult(sql,
				CollectionUtils.list(context.getWhereParameter(FieldConstant.START_TIME),
						context.getWhereParameter(FieldConstant.LIMIT_SIZE)));
	}

	@Override
	public MapperResult pageFindConfigHistoryFetchRows(MapperContext context) {
		String dataId = (String) context.getWhereParameter(FieldConstant.DATA_ID);
		String groupId = (String) context.getWhereParameter(FieldConstant.GROUP_ID);
		String tenantId = (String) context.getWhereParameter(FieldConstant.TENANT_ID);
		
		List<Object> sqlArgs = new ArrayList<>();
		sqlArgs.add(dataId);
		sqlArgs.add(groupId);
		sqlArgs.add(tenantId);
		
		String sql =
				"SELECT nid,data_id,group_id,tenant_id,app_name,src_ip,src_user,op_type,gmt_create,gmt_modified FROM his_config_info "
						+ " WHERE data_id = ? AND group_id = ? AND  tenant_id = NVL(?, '"+ NamespaceUtil.getNamespaceDefaultId() +"') "
						+ " ORDER BY nid DESC OFFSET " + context.getStartRow() + " ROWS FETCH NEXT " + context
						.getPageSize() + " ROWS ONLY ";
		return new MapperResult(sql, sqlArgs);
	}
	
	@Override
	public MapperResult findConfigHistoryFetchRows(MapperContext context) {
		String dataId = (String) context.getWhereParameter(FieldConstant.DATA_ID);
		String groupId = (String) context.getWhereParameter(FieldConstant.GROUP_ID);
		String tenantId = (String) context.getWhereParameter(FieldConstant.TENANT_ID);
		
		List<Object> sqlArgs = new ArrayList<>();
		sqlArgs.add(dataId);
		sqlArgs.add(groupId);
		sqlArgs.add(tenantId);
		
		String sqlBuilder =
				"SELECT nid,data_id,group_id,tenant_id,app_name,src_ip,src_user,op_type,gmt_create,gmt_modified FROM his_config_info "
						+ " WHERE data_id = ? AND group_id = ? " + " AND tenant_id = NVL(?,'" + NamespaceUtil
						.getNamespaceDefaultId() + "') " + " ORDER BY nid DESC";
		return new MapperResult(sqlBuilder, sqlArgs);
	}
}
